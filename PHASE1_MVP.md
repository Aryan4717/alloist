# Alloist Phase 1 MVP

Phase 1 delivers a working AI permission layer: token minting, policy evaluation, enforcement SDK, and evidence export.

![Phase 1 Architecture](assest/phase1.png)

## What Phase 1 Includes

1. **Token Service** – Mints signed capability tokens (JWTs), revocation, JWKS
2. **Policy Service** – Evaluates actions against JSON policies (allow/deny), evidence export
3. **Enforcement SDK** – Python SDK that wraps agent actions and checks policy before execution
4. **Demos** – Gmail block (deny `gmail.send`), Stripe block (deny `stripe.charge` > $1000)

## Project Structure

```
alloist/
├── backend/
│   ├── token_service/       # Mints tokens, revocation, JWKS (port 8000)
│   ├── policy_service/      # Policy evaluation, evidence export (port 8001)
│   └── demos/
│       ├── gmail_block_demo/    # Blocks gmail.send
│       └── stripe_block_demo/   # Blocks stripe.charge > $1000
├── packages/
│   ├── enforcement_py/      # Python SDK for enforcement
│   └── enforcement/         # Node.js SDK
```

## Quick Start

### 1. Start Services (Docker)

```bash
cd backend/token_service
docker compose up -d
```

This starts PostgreSQL, token service (8000), and policy service (8001). Wait ~10–15 seconds.

### 2. Create Signing Key (first time only)

```bash
docker compose exec token_service python -m app.cli.rotate_key
```

### 3. Run a Demo

Use a virtual environment (required on macOS with Homebrew Python):

```bash
cd /path/to/alloist
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/enforcement_py httpx
```

**Gmail block demo** (blocks `gmail.send`):

```bash
cd backend/demos/gmail_block_demo
python run_demo.py
```

**Stripe block demo** (blocks `stripe.charge` above $1000):

```bash
cd backend/demos/stripe_block_demo
python run_demo.py
```

Expected: Agent attempts action → policy denies → `Blocked: ... (evidence_id: <uuid>)`

## Running Tests

**Token service:**
```bash
cd backend/token_service
pip install -r requirements.txt
pytest tests/ -v
```

**Policy service:**
```bash
cd backend/policy_service
pip install -r requirements.txt
PYTHONPATH=. pytest tests/ -v
```

**Enforcement SDK (Python):**
```bash
cd packages/enforcement_py
pip install -e .
pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TOKEN_SERVICE_API_KEY` | `dev-api-key` | API key for token service |
| `POLICY_SERVICE_API_KEY` | `dev-api-key` | API key for policy service |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/token_service` | PostgreSQL connection |

## Demos

- **gmail_block_demo** – Agent attempts `gmail.send` → policy denies → blocked with evidence_id
- **stripe_block_demo** – Agent attempts `stripe.charge` $1500 → policy denies (amount > 1000) → blocked, exports signed evidence bundle to `stripe_block_evidence.json`

See `backend/demos/*/README.md` for detailed demo steps.

---

## API Reference

### Base URLs

| Service | Base URL |
|---------|----------|
| Token Service | `http://localhost:8000` |
| Policy Service | `http://localhost:8001` |

### Authentication

All endpoints except `GET /keys` require an API key. Add one of these headers:

- **X-API-Key**: `dev-api-key`
- **Authorization**: `Bearer dev-api-key`

Interactive docs: http://localhost:8000/docs and http://localhost:8001/docs

---

## Token Service APIs (port 8000)

### POST /tokens – Mint Token

Creates a new capability token (JWT) for an agent. The token encodes subject, scopes, and TTL.

**Headers:** `Content-Type: application/json`, `X-API-Key: dev-api-key`

**Body:**
```json
{
  "subject": "demo-agent",
  "scopes": ["email:send", "payments"],
  "ttl_seconds": 3600
}
```

**Response:** `token`, `token_id`, `expires_at`

---

### POST /tokens/revoke – Revoke Token

Invalidates a token so it can no longer be used. Broadcasts to WebSocket clients for real-time revocation.

**Body:**
```json
{
  "token_id": "<token_id from mint response>"
}
```

---

### POST /tokens/validate – Validate Token

Verifies JWT signature and checks DB status. Returns valid, status, subject, scopes, jti.

**Body:**
```json
{
  "token": "<full JWT from mint response>"
}
```

---

### GET /tokens/{token_id} – Get Token Metadata

Returns token metadata (subject, scopes, issued_at, expires_at, status) without the raw token value.

**Example:** `GET http://localhost:8000/tokens/b6a56e5f-50e8-421e-9133-cccf56d28250`

---

### GET /keys – JWKS (Public Keys)

Returns public keys for JWT verification. **No auth required.**

---

## Policy Service APIs (port 8001)

### POST /policy – Create Policy

Creates a policy that defines allow/deny rules for actions.

**Body – deny gmail.send:**
```json
{
  "name": "Block Gmail send",
  "description": "Deny gmail.send for demo",
  "rules": {
    "effect": "deny",
    "match": { "service": "gmail", "action_name": "send" },
    "conditions": []
  }
}
```

**Body – deny stripe.charge > 1000:**
```json
{
  "name": "Block large Stripe charges",
  "description": "Deny stripe.charge when amount > 1000",
  "rules": {
    "effect": "deny",
    "match": { "service": "stripe", "action_name": "charge" },
    "conditions": [
      { "field": "metadata.amount", "operator": "gt", "value": 1000 }
    ]
  }
}
```

---

### POST /policy/evaluate – Evaluate Policy

Checks whether an action is allowed for a given token. Returns allowed, policy_id, reason.

**Body (gmail):**
```json
{
  "token_id": "<token_id from mint>",
  "action": {
    "service": "gmail",
    "name": "send",
    "metadata": {}
  }
}
```

**Body (stripe):**
```json
{
  "token_id": "<token_id>",
  "action": {
    "service": "stripe",
    "name": "charge",
    "metadata": { "amount": 1500 }
  }
}
```

---

### GET /policy – List Policies

Returns all stored policies.

---

### POST /evidence/create – Create Evidence

Stores a signed evidence record when an action is blocked. Used by the enforcement SDK.

**Body:**
```json
{
  "evidence_id": "<uuid>",
  "action_name": "gmail.send",
  "token_snapshot": { "kid": "...", "token_id": "...", "scopes": [...] },
  "policy_id": "<uuid or null>",
  "result": "deny",
  "runtime_metadata": {}
}
```

---

### POST /evidence/export – Export Evidence

Exports a signed evidence bundle for auditors. Returns bundle, signature, public_key.

**Body:**
```json
{
  "evidence_id": "<evidence_id from blocked action>"
}
```

---

### GET /evidence/keys – Evidence Keys

Returns the public key for verifying evidence signatures.

---

## API Testing with Postman

### Suggested Flow

1. **Mint token** → `POST /tokens` → copy `token_id` and `token`
2. **Create policy** → `POST /policy` (e.g. deny gmail.send)
3. **Evaluate policy** → `POST /policy/evaluate` with token_id and action
4. **Validate token** → `POST /tokens/validate` with full JWT
5. **Export evidence** → `POST /evidence/export` with evidence_id (after running a demo that blocks)

### Database Connection (for GUI tools)

| Field | Value |
|-------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `token_service` |
| User | `postgres` |
| Password | `postgres` |

Tools: pgAdmin, TablePlus, DBeaver, Postico.

---

## API Summary

| API | Purpose |
|-----|---------|
| **Mint token** | Issue a JWT for an agent |
| **Revoke token** | Invalidate a token |
| **Validate token** | Check token validity and status |
| **Get token** | Fetch token metadata |
| **JWKS** | Public keys for JWT verification |
| **Create policy** | Define allow/deny rules |
| **Evaluate policy** | Decide if an action is allowed |
| **List policies** | List all policies |
| **Create evidence** | Record a blocked action |
| **Export evidence** | Get signed evidence bundle for auditing |
| **Evidence keys** | Public key for evidence verification |
