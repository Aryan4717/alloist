# Alloist Demos

Standalone demo scripts that simulate AI agent actions and demonstrate enforcement behavior.

## Prerequisites

1. Start services:
   ```bash
   cd backend/token_service
   docker compose up -d
   ```

2. Create signing key (first run only):
   ```bash
   docker compose exec token_service python -m app.cli.rotate_key
   ```

3. Install dependencies (from repo root):
   ```bash
   pip install -r demos/requirements.txt
   ```

## Demos

| Script | Description |
|--------|-------------|
| `gmail_demo.py` | Gmail send – policy denies gmail.send |
| `stripe_demo.py` | Stripe payment – policy denies stripe.charge when amount > 1000 |
| `revoke_demo.py` | Token revocation – allow, revoke, then block |
| `consent_demo.py` | Consent flow – require_consent, simulate user approval |

Each demo prints: **action**, **policy result**, **evidence_id**.

## Run

```bash
# From repo root
python demos/gmail_demo.py
python demos/stripe_demo.py
python demos/revoke_demo.py
python demos/consent_demo.py
```

## Environment

| Variable | Default |
|----------|---------|
| `TOKEN_SERVICE_URL` | http://localhost:8000 |
| `POLICY_SERVICE_URL` | http://localhost:8001 |
| `TOKEN_SERVICE_API_KEY` | dev-api-key |
| `POLICY_SERVICE_API_KEY` | dev-api-key |
