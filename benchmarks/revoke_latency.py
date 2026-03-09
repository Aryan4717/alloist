#!/usr/bin/env python3
"""
Benchmark: Revocation broadcast latency.
Simulate N WebSocket clients, measure median/p95 latency from revoke API to client receipt.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path

# Add enforcement_py for optional use; benchmarks work standalone with httpx/websockets
_repo = Path(__file__).resolve().parents[1]
_enforcement = _repo / "packages" / "enforcement_py"
if _enforcement.exists():
    sys.path.insert(0, str(_enforcement))


async def connect_client(ws_url: str, receive_times: list, target_token_id: str) -> None:
    """Connect to WebSocket, wait for revocation of target_token_id, record receive time."""
    import websockets

    t_receive: float | None = None

    async def handler(ws):
        nonlocal t_receive
        async for msg in ws:
            try:
                data = json.loads(msg)
                if data.get("event") == "revoked" and data.get("token_id") == target_token_id:
                    t_receive = time.perf_counter()
                    return
            except (json.JSONDecodeError, KeyError):
                pass

    async with websockets.connect(ws_url, close_timeout=2) as ws:
        await handler(ws)

    if t_receive is not None:
        receive_times.append(t_receive)


async def run_benchmark(
    host: str,
    clients: int,
    api_key: str,
    connect_wait: float = 2.0,
) -> dict:
    base = host.rstrip("/").replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{base}/ws/revocations"
    http_base = host.rstrip("/").replace("ws://", "http://").replace("wss://", "https://")

    import httpx

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    # 1. Mint token
    with httpx.Client(timeout=30.0) as client:
        mint_resp = client.post(
            f"{http_base}/tokens",
            json={"subject": "bench", "scopes": ["read"], "ttl_seconds": 3600},
            headers=headers,
        )
    if mint_resp.status_code != 200:
        raise RuntimeError(f"Mint failed: {mint_resp.status_code} {mint_resp.text}")
    token_id = mint_resp.json()["token_id"]

    # 2. Connect clients (start tasks)
    receive_times: list[float] = []
    tasks = [
        asyncio.create_task(connect_client(ws_url, receive_times, str(token_id)))
        for _ in range(clients)
    ]

    # Allow connections to establish
    await asyncio.sleep(connect_wait)

    # Verify connection count (optional)
    with httpx.Client(timeout=10.0) as client:
        stats_resp = client.get(f"{http_base}/revocations/stats", headers=headers)
    if stats_resp.status_code == 200:
        connected = stats_resp.json().get("connected_count", 0)
        if connected < clients:
            print(f"Warning: only {connected}/{clients} connected", file=sys.stderr)

    # 3. Revoke and measure
    t0 = time.perf_counter()
    with httpx.Client(timeout=30.0) as client:
        revoke_resp = client.post(
            f"{http_base}/tokens/revoke",
            json={"token_id": token_id},
            headers=headers,
        )
    if revoke_resp.status_code != 200:
        raise RuntimeError(f"Revoke failed: {revoke_resp.status_code} {revoke_resp.text}")

    # 4. Wait for clients to receive (with timeout)
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=10.0)
    except asyncio.TimeoutError:
        pass

    # 5. Compute latencies (t_receive - t0)
    latencies_ms = [(t - t0) * 1000 for t in receive_times]

    if not latencies_ms:
        return {
            "median_ms": None,
            "p95_ms": None,
            "connected": clients,
            "received": 0,
            "error": "no clients received revocation",
        }

    latencies_ms.sort()
    p95_idx = int(len(latencies_ms) * 0.95) - 1
    p95_idx = max(0, p95_idx)

    return {
        "median_ms": round(statistics.median(latencies_ms), 2),
        "p95_ms": round(latencies_ms[p95_idx], 2),
        "connected": clients,
        "received": len(latencies_ms),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Revocation broadcast latency benchmark")
    parser.add_argument("--host", default="http://localhost:8000", help="Token service URL")
    parser.add_argument("--clients", type=int, default=1000, help="Number of WebSocket clients")
    parser.add_argument("--api-key", default="dev-api-key", help="API key")
    parser.add_argument("--output", help="Write JSON result to file")
    parser.add_argument("--connect-wait", type=float, default=2.0, help="Seconds to wait for WS connections")
    args = parser.parse_args()

    result = asyncio.run(
        run_benchmark(args.host, args.clients, args.api_key, connect_wait=args.connect_wait)
    )
    out = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(out)
    print(out)

    if result.get("received", 0) < args.clients * 0.9:
        print(f"Warning: only {result['received']}/{args.clients} received", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
