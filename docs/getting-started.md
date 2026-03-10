# Getting Started

This guide covers running Alloist with Docker Compose, configuring environment variables, and running backend services locally.

---

## Run Docker Compose

The fastest way to run Alloist is with Docker Compose. It starts PostgreSQL, Redis, the Token Service, and the Policy Service.

```bash
cd backend/token_service
docker compose up -d
```

**Services started:**

| Service        | Port | Description                    |
|----------------|------|--------------------------------|
| PostgreSQL     | 5432 | Database for both services     |
| Redis          | 6379 | Revocation pub/sub             |
| Token Service  | 8000 | Mint tokens, revocation, JWKS |
| Policy Service | 8001 | Policy evaluation, evidence    |

Wait ~15 seconds for services to become healthy.

### Create signing key (first time only)

The Token Service needs an Ed25519 signing key to mint JWTs. Run once after the first deploy:

```bash
docker compose exec token_service python -m app.cli.rotate_key
```

Or, if using `run` before the container is fully up:

```bash
docker compose run --rm -T token_service sh -c "alembic upgrade head && python -m app.cli.rotate_key"
```

### Verify services

- Token Service: http://localhost:8000/health
- Policy Service: http://localhost:8001/health
- Interactive API docs: http://localhost:8000/docs and http://localhost:8001/docs

---

## Environment Variables

Docker Compose uses `${VAR}` substitution from the host environment or a `.env` file in the same directory as `docker-compose.yml`. Create `backend/token_service/.env`:

```
TOKEN_SERVICE_API_KEY=dev-api-key
POLICY_SERVICE_API_KEY=dev-api-key
JWT_SECRET=change-me-in-production
```

Then run `docker compose up -d`. Docker Compose will read this file for variable substitution.

Alternatively, export variables before running:

```bash
export TOKEN_SERVICE_API_KEY=dev-api-key
export POLICY_SERVICE_API_KEY=dev-api-key
export JWT_SECRET=change-me-in-production
cd backend/token_service
docker compose up -d
```

### Common variables

| Variable                 | Default                                             | Description                        |
|--------------------------|-----------------------------------------------------|------------------------------------|
| `TOKEN_SERVICE_API_KEY`  | `dev-api-key`                                       | API key for Token Service          |
| `POLICY_SERVICE_API_KEY` | `dev-api-key`                                       | API key for Policy Service         |
| `JWT_SECRET`             | `change-me-in-production`                           | JWT signing secret (sessions, etc.)|
| `DATABASE_URL`           | (set by Compose for Docker)                         | PostgreSQL connection string       |
| `REDIS_URL`              | `redis://redis:6379/0` (Docker)                      | Redis for revocation pub/sub       |

For production secret management (AWS, Vault), see [secrets/README.md](secrets/README.md).

---

## Running Backend Services Locally

For development without Docker:

1. **Start PostgreSQL and Redis** (e.g. via Docker, Homebrew, or system services).

2. **Token Service:**
   ```bash
   cd backend/token_service
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.cli.rotate_key  # first time
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Policy Service:**
   ```bash
   cd backend/policy_service
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --host 0.0.0.0 --port 8001
   ```

4. Set `DATABASE_URL`, `REDIS_URL`, `TOKEN_SERVICE_API_KEY`, `POLICY_SERVICE_API_KEY`, and `JWT_SECRET` in your environment or `.env` file in the project root. The services load `.env` via python-dotenv when available.

---

## Next Steps

- [API Reference](api-reference.md) – Token API, Policy API, consent, SDK, evidence
- [Architecture](architecture.md) – How Alloist works
- [PHASE1_MVP.md](../PHASE1_MVP.md) – Run demos (Gmail block, Stripe block, YC demo)
