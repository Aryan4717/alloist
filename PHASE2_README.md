# Alloist Phase 2

## In Plain English (One-Read Summary)

Phase 2 adds three things:

**2.1 When the server is down** – You choose what happens: block risky actions (fail closed), allow but log them (soft fail), or allow as usual (fail open). You can pick different behavior per action (e.g. block email, allow reading logs).

**2.2 Faster “turn off” for tokens** – When you revoke a token, all agents get the update in real time via Redis instead of waiting for their next check. Revocations are signed so agents know they’re real.

**2.3 Performance checks** – Tests measure how fast revocations reach agents and how many permission checks per second the system handles. These run automatically on every push.

---

## What Phase 2 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **2.1** | `feature/fail-closed` | Fail-closed modes & offline resilience |
| **2.2** | `feature/revocation-push` | Revocation push via Redis pub/sub, signed events |
| **2.3** | `feature/scale-testing` | Scale & perf benchmarking harness, CI |

---

## 2.1 Fail-Closed Modes & Offline Resilience

When the token or policy backend is unreachable (network partition, outage), the SDK can:

- **fail_closed** – Block high-risk actions with `fail_closed_backend_unreachable`
- **soft_fail** – Allow but create high-severity evidence (`degraded_mode: "soft_fail"`)
- **fail_open** – Allow without special audit (default)
- **fail_mode_per_action** – Override per action, e.g. `{"send_email": "fail_closed", "read_logs": "soft_fail"}`

### SDK Usage (Python)

```python
from alloist_enforce import create_enforcement

enforcement = create_enforcement(
    api_url="http://localhost:8000",
    api_key="dev-api-key",
    fail_mode="fail_closed",  # or "soft_fail", "fail_open"
    fail_mode_per_action={"send_email": "fail_closed", "read_logs": "soft_fail"},
)
```

### Tests

```bash
cd packages/enforcement_py
pip install -e ".[dev]"   # installs package + pytest
python -m pytest tests/test_enforcement.py -v -k "fail_closed or soft_fail or fail_mode"
```

---

## 2.2 Revocation Push System

Revocation events are published to Redis and broadcast to SDKs in real time.

### Components

- **Redis** – Pub/sub channel for revocation events
- **Token service** – Publishes signed payloads on revoke; falls back to direct broadcast if Redis is down
- **SDK** – Subscribes to WebSocket, verifies signed payloads, re-checks revoked before allowing

### Prerequisites

- Redis (port 6379) – included in `backend/token_service/docker-compose.yml`

### Start Services (with Redis)

```bash
cd backend/token_service
docker compose up -d
# Wait ~15s, then create signing key:
docker compose run --rm -T --entrypoint "" token_service sh -c "alembic upgrade head && python -m app.cli.rotate_key"
```

### Verify

```bash
# Mint token
curl -X POST http://localhost:8000/tokens \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"subject":"test","scopes":["read"],"ttl_seconds":60}'

# Revoke (publishes to Redis)
curl -X POST http://localhost:8000/tokens/revoke \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"token_id":"<token_id from above>"}'
```

### Tests

```bash
cd backend/token_service
pip install -r requirements.txt
python -m pytest tests/test_revocation_pubsub.py tests/test_revocation_integration.py -v
```

---

## 2.3 Scale & Perf Testing

Benchmarks for revocation latency and agent throughput.

### Prerequisites

- Token service running (port 8000)
- Signing key created

### Run Benchmarks

```bash
pip install -r benchmarks/requirements.txt
pip install -e packages/enforcement_py
```

**Revocation latency** (WebSocket clients, measure p95 latency):

```bash
python benchmarks/revoke_latency.py --host http://localhost:8000 --clients 20 --connect-wait 5 --api-key dev-api-key --output revoke_result.json
```

**Agent throughput** (concurrent policy checks):

```bash
python benchmarks/agent_throughput.py --host http://localhost:8000 --workers 20 --duration 5 --api-key dev-api-key --output agent_result.json
```

### CI Perf Job

`.github/workflows/perf.yml` runs on push to `feature/scale-testing` and `main`:

1. Starts services (Docker)
2. Creates signing key
3. Runs revoke latency (20 clients)
4. Runs agent throughput (20 workers, 5s)
5. Asserts: p95 < 10000ms, throughput > 1 checks/s
6. Uploads `perf_results.json` as artifact

### Thresholds

| Metric | Threshold |
|--------|-----------|
| Revoke p95 | < 10000 ms |
| Throughput | > 1 checks/s |

---

## Full Testing Checklist

### Phase 2.1 (Fail-Closed)

- [ ] `cd packages/enforcement_py && pip install -e ".[dev]" && python -m pytest tests/ -v -k "fail_closed or soft_fail or fail_mode"`
- [ ] `cd packages/enforcement && npm test` (Node SDK)

### Phase 2.2 (Revocation Push)

- [ ] `cd backend/token_service && docker compose up -d` (ensure Redis + token_service)
- [ ] Create signing key
- [ ] `pytest tests/test_revocation_pubsub.py tests/test_revocation_integration.py -v`
- [ ] Mint token, revoke, confirm WebSocket clients receive event

### Phase 2.3 (Scale Testing)

- [ ] `cd benchmarks && python revoke_latency.py --clients 20`
- [ ] `cd benchmarks && python agent_throughput.py --workers 20 --duration 5`
- [ ] Push to `feature/scale-testing` and confirm perf job passes

---

## Environment Variables (Phase 2)

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for revocation pub/sub |
| `TOKEN_SERVICE_API_KEY` | `dev-api-key` | API key for token service |
| `DATABASE_URL` | (see Phase 1) | PostgreSQL |

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/fail-closed` | Fail-closed, soft_fail, fail_mode_per_action |
| `feature/revocation-push` | Redis pub/sub, signed revocation events |
| `feature/scale-testing` | Benchmarks, perf CI |
