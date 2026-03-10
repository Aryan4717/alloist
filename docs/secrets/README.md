# Secure Secret Management

Alloist uses a unified secret loader that supports environment variables, AWS Secrets Manager, and Hashicorp Vault. Secrets are loaded in cascade order, masked in logs, sanitized in stack traces, and optionally refreshed in the background.

## Quick start

```python
from alloist_secrets import get, validate_required

# Cascade: env -> AWS -> Vault
value = get("TOKEN_SERVICE_API_KEY")

# Startup validation - raises MissingSecretError if missing
validate_required(["DATABASE_URL", "TOKEN_SERVICE_API_KEY"])
```

## Providers (cascade order)

Secrets are resolved in this order; the first non-empty value wins:

1. **Environment variables** – `os.environ` plus optional `.env` file (python-dotenv)
2. **AWS Secrets Manager** – when `SECRET_PROVIDER_AWS` is enabled
3. **Hashicorp Vault** – when `SECRET_PROVIDER_VAULT` is enabled

### Environment variables (default)

- Reads from `os.environ`
- If a `.env` file exists and the value is not already set, it is loaded via python-dotenv
- No extra configuration required

### AWS Secrets Manager

| Variable | Description |
|----------|-------------|
| `SECRET_PROVIDER_AWS` | Set to `1` or `true` to enable |
| `AWS_SECRET_NAME` | Secret name; value should be a JSON object whose keys map to secret names (e.g. `TOKEN_SERVICE_API_KEY`, `DATABASE_URL`) |
| `SECRET_<KEY>_AWS_ID` | Optional: overrides the secret ID for a specific key |

Requires `boto3` (or `alloist-secrets[aws]`).

### Hashicorp Vault

| Variable | Description |
|----------|-------------|
| `SECRET_PROVIDER_VAULT` | Set to `1` or `true` to enable |
| `VAULT_ADDR` | Vault server URL |
| `VAULT_TOKEN` | Authentication token |
| `VAULT_SECRET_PATH` | Default path prefix (default: `alloist`) |
| `SECRET_<KEY>_VAULT_PATH` | Optional: overrides the path for a specific key |

Requires `hvac` (or `alloist-secrets[vault]`).

## Rotation

Set `SECRET_REFRESH_INTERVAL_SEC` (e.g. `300`) to enable background rotation for secrets loaded from AWS or Vault. A background thread periodically re-fetches those secrets and updates the in-memory cache.

- Env vars are not refreshed (they are read once)
- Only secrets originally loaded from AWS or Vault are re-fetched

## Safety features

- **Log redaction**: Secret values are replaced with `***` in structlog output. Use `register_secret_key("TOKEN_SERVICE_API_KEY")` for custom keys.
- **Stack trace sanitization**: Exception strings are sanitized to avoid leaking `api_key=...`, `password=...`, etc.

## Docker setup

The services no longer depend on an `env_file` pointing to a `.env` file. Secrets are passed via environment variables.

### Passing secrets to containers

**1. Host environment + Docker Compose variable substitution**

Create a `.env` file in `backend/token_service/` (same directory as `docker-compose.yml`). Docker Compose reads it for `${VAR}` substitution:

```bash
# backend/token_service/.env
TOKEN_SERVICE_API_KEY=your-api-key
POLICY_SERVICE_API_KEY=your-api-key
JWT_SECRET=your-jwt-secret
```

Then run:

```bash
cd backend/token_service
docker compose up -d
```

**2. Export before running**

```bash
export TOKEN_SERVICE_API_KEY=dev-api-key
export POLICY_SERVICE_API_KEY=dev-api-key
export JWT_SECRET=change-me-in-production
cd backend/token_service
docker compose up -d
```

**3. Docker secrets**

For production, use Docker secrets and a startup script that reads them:

```yaml
# Example: mount secrets and read at startup
services:
  token_service:
    secrets:
      - token_service_api_key
    entrypoint: ["/bin/sh", "-c", "export TOKEN_SERVICE_API_KEY=$(cat /run/secrets/token_service_api_key) && alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

secrets:
  token_service_api_key:
    external: true
```

### Required variables

| Variable | Token Service | Policy Service |
|----------|---------------|----------------|
| `DATABASE_URL` | Required | Required |
| `TOKEN_SERVICE_API_KEY` | Required (empty OK for dev) | - |
| `POLICY_SERVICE_API_KEY` | - | Required (empty OK for dev) |
| `JWT_SECRET` | Required | Required |
| `REDIS_URL` | Optional | - |
| `REVOCATION_SIGNING_*` | Optional | - |
| `EVIDENCE_SIGNING_*` | - | Optional |

## Local development

- A `.env` file in the project root or working directory is loaded by the env provider if values are not already in `os.environ`
- For Docker: create `backend/token_service/.env` with the variables above, or export them before `docker compose up`
