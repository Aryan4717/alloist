# Alloist Phase 7

## In Plain English (One-Read Summary)

Phase 7 makes Alloist **observable and secure in production**:

**7.1 Logging** – Structured JSON logs that work with Datadog, ELK, and OpenTelemetry. Every request is logged with method, path, status, and latency. Secrets are automatically redacted in logs and stack traces so you never leak API keys or passwords.

**7.2 Monitoring** – Prometheus metrics for every important operation: tokens minted, policy evaluations, enforcement checks, revocations, consent requests. Plus health and readiness probes for Kubernetes. Add Grafana for dashboards.

**7.3 Secrets** – A unified secret loader. Use env vars, AWS Secrets Manager, or Hashicorp Vault—they cascade in that order. Secrets are validated at startup (fail fast if missing). Optional background rotation refreshes them without restarting. Docker no longer relies on `.env` files; pass secrets via env or Docker secrets.

---

## What Phase 7 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **7.1** | `feature/logging` | Structured JSON logging, middleware, secret redaction, exception sanitization |
| **7.2** | `feature/monitoring` | Prometheus metrics, health/ready endpoints, middleware |
| **7.3** | `feature/secrets` | Secret loader (env/AWS/Vault), rotation, startup validation, log redaction integration |

---

## 7.1 Logging

Structured JSON logging for all backend services. Compatible with Datadog, ELK, and OpenTelemetry collectors.

### In plain English

- **JSON logs** – Every log line is a JSON object. Fields like `level`, `timestamp`, `event`, `service`, `method`, `path`, `status`, `duration_ms` are machine-parsable.
- **Request middleware** – Automatically logs each HTTP request with method, path, status, and latency.
- **Secret redaction** – Values for keys like `api_key`, `password`, `token` are replaced with `***` in logs. Use `register_secret_key()` for custom keys (e.g. `TOKEN_SERVICE_API_KEY`).
- **Stack trace sanitization** – Exception strings are sanitized so `api_key=xyz` in tracebacks becomes `api_key=***`. Prevents leaking secrets when errors are logged.

### Package

**Location**: `packages/structured_logging/`

### Usage

```python
from alloist_logging import get_logger, log_event, logging_middleware

# In main.py - add middleware first (before CORS)
app.add_middleware(logging_middleware("token_service"))

# In routes
logger = get_logger("token_service")
log_event(logger, action="token_created", result="success", org_id=str(ctx.org_id))
```

### Install

```bash
pip install -e ../../packages/structured_logging
```

### Configuration

The logging package auto-configures structlog with JSON output. No env vars required. Secret redaction and exception sanitization are enabled by default.

---

## 7.2 Monitoring

Prometheus metrics and health endpoints for liveness and readiness probes.

### In plain English

- **Prometheus metrics** – Counters and histograms for enforcement checks, policy evaluations, token issuance, revocations, consent requests, and HTTP request latency.
- **`/metrics`** – Exposes metrics in Prometheus exposition format. Scrape this endpoint to collect data.
- **`/health`** – Liveness probe. Returns 200 if the process is up.
- **`/ready`** – Readiness probe. Returns 200 if DB is reachable, 503 otherwise. Use this for Kubernetes readiness checks.

### Package

**Location**: `packages/backend_metrics/`

### Usage

```python
from alloist_metrics import create_metrics, get_metrics_output, metrics_middleware, health_router

# In main.py
app.add_middleware(metrics_middleware("token_service"))

@app.get("/metrics")
def metrics():
    return Response(content=get_metrics_output(), media_type="text/plain; version=0.0.4")

app.include_router(health_router(check_ready=db_ping))

# In routes
metrics = create_metrics("token_service")
metrics.inc_token_issuance()
```

### Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `enforcement_checks_total` | Counter | Enforcement checks (X-Request-Type) |
| `policy_evaluations_total` | Counter | Policy evaluations |
| `token_issuance_total` | Counter | Tokens minted |
| `revocation_events_total` | Counter | Tokens revoked |
| `consent_requests_total` | Counter | Consent requests created |
| `enforcement_latency_ms` | Histogram | Latency of enforcement checks |
| `policy_evaluation_latency_ms` | Histogram | Latency of policy evaluations |
| `http_request_duration_ms` | Histogram | HTTP request latency by method, path, status |

### Prometheus scrape config

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "alloist-token-service"
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: /metrics

  - job_name: "alloist-policy-service"
    static_configs:
      - targets: ["localhost:8001"]
    metrics_path: /metrics
```

### Install

```bash
pip install -e ../../packages/backend_metrics
```

### Documentation

See [docs/monitoring/README.md](docs/monitoring/README.md) for full Prometheus + Grafana setup and example queries.

---

## 7.3 Secrets

Unified secret management with cascade lookup, optional rotation, and safety features.

### In plain English

- **Cascade** – Env vars → AWS Secrets Manager → Vault. First non-empty value wins.
- **Startup validation** – `validate_required(["DATABASE_URL", "JWT_SECRET"])` runs at startup. If any secret is missing, the service fails before accepting requests.
- **Rotation** – Set `SECRET_REFRESH_INTERVAL_SEC` (e.g. 300). A background thread periodically re-fetches secrets from AWS or Vault. No restart needed.
- **Safety** – Secrets are masked in logs (via `register_secret_key`) and sanitized in stack traces.
- **Docker** – No `env_file` dependency. Pass secrets via environment or Docker secrets. Variable substitution works with `.env` in the compose directory.

### Package

**Location**: `packages/alloist_secrets/`

### Usage

```python
from alloist_secrets import get, validate_required, register_secret_key, start_rotation

# Get secret (cascade: env → AWS → Vault)
value = get("TOKEN_SERVICE_API_KEY")

# Startup validation - raises MissingSecretError if missing
validate_required(["DATABASE_URL", "JWT_SECRET"])
validate_required(["TOKEN_SERVICE_API_KEY"], allow_empty=True)  # Allow empty for dev

# Register keys for log redaction (integrated with structured_logging)
register_secret_key("TOKEN_SERVICE_API_KEY")

# Start background rotation (if SECRET_REFRESH_INTERVAL_SEC is set)
start_rotation()
```

### Providers

| Provider | Enable | Config |
|----------|--------|--------|
| **Env** | Default | `os.environ` + optional `.env` file (python-dotenv) |
| **AWS** | `SECRET_PROVIDER_AWS=1` | `AWS_SECRET_NAME` (JSON secret), optional `SECRET_<KEY>_AWS_ID` |
| **Vault** | `SECRET_PROVIDER_VAULT=1` | `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_SECRET_PATH` |

### Required secrets per service

| Secret | Token Service | Policy Service |
|--------|---------------|----------------|
| `DATABASE_URL` | Required | Required |
| `TOKEN_SERVICE_API_KEY` | Required (empty OK for dev) | - |
| `POLICY_SERVICE_API_KEY` | - | Required (empty OK for dev) |
| `JWT_SECRET` | Required | Required |
| `REDIS_URL` | Optional | - |
| `REVOCATION_SIGNING_*` | Optional | - |
| `EVIDENCE_SIGNING_*` | - | Optional |

### Docker setup

Create `backend/token_service/.env` (or export vars):

```
TOKEN_SERVICE_API_KEY=dev-api-key
POLICY_SERVICE_API_KEY=dev-api-key
JWT_SECRET=change-me-in-production
```

Then:

```bash
cd backend/token_service
docker compose up -d
```

### Install

```bash
pip install -e ../../packages/alloist_secrets
# Optional: pip install boto3  # for AWS
# Optional: pip install hvac   # for Vault
```

### Documentation

See [docs/secrets/README.md](docs/secrets/README.md) for full provider config, rotation, and Docker secrets pattern.

---

## Project Structure (Phase 7 Additions)

```
alloist/
├── packages/
│   ├── structured_logging/    # 7.1 Logging
│   │   ├── alloist_logging/
│   │   │   ├── config.py      # structlog + processors
│   │   │   ├── middleware.py
│   │   │   └── processors.py  # secret_redacting, sanitize_exception
│   │   └── pyproject.toml
│   ├── backend_metrics/       # 7.2 Monitoring
│   │   ├── alloist_metrics/
│   │   │   ├── middleware.py
│   │   │   ├── prometheus.py
│   │   │   ├── health.py      # /health, /ready
│   │   │   └── __init__.py
│   │   └── pyproject.toml
│   └── alloist_secrets/       # 7.3 Secrets
│       ├── alloist_secrets/
│       │   ├── loader.py      # cascade logic
│       │   ├── providers/     # env, aws, vault
│       │   ├── rotation.py    # background refresh
│       │   ├── redaction.py   # register_secret_key
│       │   └── __init__.py
│       └── pyproject.toml
├── docs/
│   ├── monitoring/README.md   # Prometheus, Grafana
│   └── secrets/README.md      # Providers, Docker, rotation
└── backend/
    ├── token_service/         # Uses all three packages
    │   ├── app/config.py     # secrets.get() for secret fields
    │   ├── app/main.py       # logging, metrics, validate_required, start_rotation
    │   └── docker-compose.yml # No env_file; env var substitution
    └── policy_service/        # Same
```

---

## Full Testing Checklist (Phase 7)

### 7.1 Logging

- [ ] Start services; confirm JSON logs in stdout (each line is valid JSON)
- [ ] Log a message with `api_key=secret123`; confirm it appears as `api_key=***`
- [ ] Trigger an error with secret in traceback; confirm exception string is sanitized
- [ ] Run tests: `cd packages/structured_logging && pytest tests/ -v`

### 7.2 Monitoring

- [ ] `curl http://localhost:8000/metrics` returns Prometheus format
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8000/ready` returns 200 when DB is up, 503 when DB is down
- [ ] Mint a token; confirm `token_issuance_total` increases
- [ ] Check [docs/monitoring/README.md](docs/monitoring/README.md) for Grafana setup

### 7.3 Secrets

- [ ] Start without `JWT_SECRET`; service should fail at startup with `MissingSecretError`
- [ ] Create `backend/token_service/.env` with required vars; `docker compose up -d` succeeds
- [ ] With `SECRET_REFRESH_INTERVAL_SEC=300`, confirm rotation thread starts (check logs)
- [ ] Run services; confirm no secrets in logs or error messages
- [ ] Run token service tests: `cd backend/token_service && pytest tests/ -v`
- [ ] Run policy service tests: `cd backend/policy_service && pytest tests/ -v`

---

## Environment Variables (Phase 7)

### Logging

No env vars required. Secret redaction uses `register_secret_key()` from config.

### Monitoring

No env vars required for basic setup. Prometheus scrapes `/metrics`.

### Secrets

| Variable | Description |
|----------|-------------|
| `SECRET_PROVIDER_AWS` | Set to `1` or `true` to enable AWS |
| `AWS_SECRET_NAME` | AWS Secrets Manager secret name (JSON) |
| `SECRET_PROVIDER_VAULT` | Set to `1` or `true` to enable Vault |
| `VAULT_ADDR` | Vault server URL |
| `VAULT_TOKEN` | Vault auth token |
| `VAULT_SECRET_PATH` | Default Vault path prefix |
| `SECRET_REFRESH_INTERVAL_SEC` | Background refresh interval (seconds); 0 = disabled |
| `TOKEN_SERVICE_API_KEY` | Token service API key |
| `POLICY_SERVICE_API_KEY` | Policy service API key |
| `JWT_SECRET` | JWT signing secret |
| `DATABASE_URL` | PostgreSQL connection string |

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/logging` | Structured JSON logging, middleware, secret redaction, exception sanitization |
| `feature/monitoring` | Prometheus metrics, health/ready endpoints, middleware |
| `feature/secrets` | Secret loader (env/AWS/Vault), rotation, startup validation, Docker env injection |

---

## Consistency with Phase 1–6

Phase 7 follows the same structure:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification
- **Environment / structure** – Where things live
- **Branch summary** – Quick reference

Phase 7 is about **observability and security**: structured logs for debugging and compliance, metrics for dashboards and alerts, and a safe way to manage secrets in dev and production.
