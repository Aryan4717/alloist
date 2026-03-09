#!/usr/bin/env python3
"""
Benchmark: Policy check throughput.
Simulate many concurrent agent actions (enforcement check) and measure checks/sec.
"""

import argparse
import concurrent.futures
import json
import sys
import time
from pathlib import Path

# Add enforcement_py
_repo = Path(__file__).resolve().parents[1]
_enforcement = _repo / "packages" / "enforcement_py"
if _enforcement.exists():
    sys.path.insert(0, str(_enforcement))

import httpx


def worker(
    token: str,
    api_url: str,
    api_key: str,
    duration_sec: float,
) -> tuple[int, int]:
    """Run check() in a loop for duration_sec. Returns (checks, errors)."""
    from cognara_enforce import create_enforcement

    enforcement = create_enforcement(
        api_url=api_url,
        api_key=api_key,
        fail_closed=False,
    )
    checks = 0
    errs = 0
    end = time.perf_counter() + duration_sec
    while time.perf_counter() < end:
        try:
            enforcement.check(
                token,
                action_name="send_email",
                metadata={"to": "bench@example.com"},
            )
            checks += 1
        except Exception:
            errs += 1
    enforcement.close()
    return (checks, errs)


def run_benchmark(
    host: str,
    workers: int,
    duration_sec: float,
    api_key: str,
) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    # 1. Mint token
    with httpx.Client(timeout=30.0) as client:
        mint_resp = client.post(
            f"{host.rstrip('/')}/tokens",
            json={"subject": "bench", "scopes": ["email:send"], "ttl_seconds": 3600},
            headers=headers,
        )
    if mint_resp.status_code != 200:
        raise RuntimeError(f"Mint failed: {mint_resp.status_code} {mint_resp.text}")
    token = mint_resp.json()["token"]

    # 2. Run workers
    start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(
                worker,
                token,
                host.rstrip("/"),
                api_key,
                duration_sec,
            )
            for _ in range(workers)
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    elapsed = time.perf_counter() - start
    total = sum(r[0] for r in results)
    total_errors = sum(r[1] for r in results)

    return {
        "throughput_checks_per_sec": round(total / elapsed, 2) if elapsed > 0 else 0,
        "total_checks": total,
        "elapsed_sec": round(elapsed, 2),
        "workers": workers,
        "errors": total_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent policy check throughput benchmark")
    parser.add_argument("--host", default="http://localhost:8000", help="Token service URL")
    parser.add_argument("--workers", type=int, default=50, help="Concurrent workers")
    parser.add_argument("--duration", type=float, default=10.0, help="Run duration (seconds)")
    parser.add_argument("--api-key", default="dev-api-key", help="API key")
    args = parser.parse_args()

    result = run_benchmark(
        args.host,
        args.workers,
        args.duration,
        args.api_key,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
