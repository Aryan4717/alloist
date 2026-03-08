# Token Service

FastAPI microservice that mints signed capability tokens (Ed25519 JWT), stores them in PostgreSQL, and supports key rotation.

## Prerequisites

- Docker and Docker Compose (for local run)
- Python 3.11+ (for local development)

## Quick Start with Docker

```bash
# From backend/token_service/
docker-compose up -d

# Create an initial signing key (required before minting tokens)
docker-compose exec token_service python -m app.cli.rotate_key
```

The API will be available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## Local Development

### 1. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run migrations

```bash
alembic upgrade head
```

### 4. Create signing key

```bash
python -m app.cli.rotate_key
```

### 5. Run the app

```bash
export TOKEN_SERVICE_API_KEY=your-secret-api-key
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (default: `postgresql://postgres:postgres@localhost:5432/token_service`) |
| `TOKEN_SERVICE_API_KEY` | API key for authenticating requests (required) |

## API Endpoints

### Public (no auth)

- **GET /keys** — JSON Web Key Set (JWKS) for JWT verification. Used by enforcement SDK.

### Protected (API key via `X-API-Key` or `Authorization: Bearer <key>`)

### Mint token

```bash
curl -X POST http://localhost:8000/tokens \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"subject": "user123", "scopes": ["read", "write"], "ttl_seconds": 3600}'
```

Response: `{ "token": "...", "token_id": "uuid", "expires_at": "..." }`

### Revoke token

```bash
curl -X POST http://localhost:8000/tokens/revoke \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"token_id": "uuid-from-mint-response"}'
```

### Get token metadata

```bash
curl http://localhost:8000/tokens/{token_id} \
  -H "X-API-Key: your-secret-api-key"
```

Returns metadata (id, subject, scopes, issued_at, expires_at, status) — no raw token value.

### Validate token

```bash
curl -X POST http://localhost:8000/tokens/validate \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJ..."}'
```

Returns `{ "valid": bool, "status": "active"|"revoked", "subject": str, "scopes": [...], "jti": str }`.

### WebSocket: Revocation push

Connect to `ws://localhost:8000/ws/revocations` to receive real-time revocation events. On revoke, clients receive `{ "token_id": "uuid", "event": "revoked" }`.

## Key Rotation

```bash
python -m app.cli.rotate_key
```

Generates a new Ed25519 signing key, marks it active, and deactivates the previous key. Existing tokens remain valid (verified with their original key via `kid`).

## Run Tests

```bash
pytest tests/ -v
```
