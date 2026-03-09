# Benchmarking Harness

Scale and performance tests for revocation broadcast and policy check throughput.

## Prerequisites

- Token service running (port 8000)

```bash
cd backend/token_service && docker compose up -d
```

## Installation

```bash
pip install -r benchmarks/requirements.txt
pip install -e packages/enforcement_py
```

## Revocation Broadcast Latency

Simulates N WebSocket clients subscribing to the revocation channel, mints a token, revokes it, and measures median/p95 latency from revoke API call to client receipt.

```bash
python benchmarks/revoke_latency.py [--host URL] [--clients N] [--api-key KEY]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `http://localhost:8000` | Token service URL |
| `--clients` | `1000` | Number of WebSocket clients |
| `--api-key` | `dev-api-key` | API key for mint/revoke |

**Output** (JSON): `median_ms`, `p95_ms`, `connected`, `received`

## Agent Throughput

Simulates many concurrent agents running policy checks and measures checks per second.

```bash
python benchmarks/agent_throughput.py [--host URL] [--workers N] [--duration SEC] [--api-key KEY]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `http://localhost:8000` | Token service URL |
| `--workers` | `50` | Concurrent workers |
| `--duration` | `10` | Run duration (seconds) |
| `--api-key` | `dev-api-key` | API key |

**Output** (JSON): `throughput_checks_per_sec`, `total_checks`, `elapsed_sec`, `workers`, `errors`

## CI Perf Sanity

The `.github/workflows/perf.yml` job runs on push to `feature/scale-testing` and `main`:

1. Starts services via docker compose
2. Runs revoke latency (100 clients)
3. Runs agent throughput (20 workers, 5s)
4. Asserts thresholds: p95 < 500ms, throughput > 50 checks/s
5. Uploads `perf_results.json` as artifact

## Thresholds

| Metric | Threshold |
|--------|-----------|
| Revoke p95 | < 500 ms |
| Throughput | > 50 checks/s |

Adjust in the workflow or scripts as needed for your environment.
