# Policy Service

Minimal policy checking service that, given token + action, returns allow/deny. Policies are stored as JSON rules in PostgreSQL.

## Features

- **POST /policy/evaluate** - Evaluate whether an action is allowed for a token
- **POST /policy** - Create a new policy
- **GET /policy** - List all policies
- CLI: `python -m app.cli.create_policy` or `policy-cli` (after `pip install -e .`)

## Quick Start

```bash
# From backend/token_service (shared docker-compose)
docker-compose up -d

# Or run policy service locally (requires Postgres + token_service migrations)
cd backend/policy_service
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/token_service
alembic upgrade head
uvicorn app.main:app --port 8001
```

## Create a Test Policy

```bash
# Via CLI
python -m app.cli.create_policy \
  --name "Block large Stripe charges" \
  --effect deny \
  --service stripe \
  --action charge \
  --condition "metadata.amount:gt:1000"

# Via API
curl -X POST http://localhost:8001/policy \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Block large Stripe charges",
    "description": "Deny stripe.charge when amount > 1000",
    "rules": {
      "effect": "deny",
      "match": {"service": "stripe", "action_name": "charge"},
      "conditions": [{"field": "metadata.amount", "operator": "gt", "value": 1000}]
    }
  }'
```

## Evaluate

```bash
curl -X POST http://localhost:8001/policy/evaluate \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "token_id": "<valid-token-uuid>",
    "action": {
      "service": "stripe",
      "name": "charge",
      "metadata": {"amount": 1500, "currency": "usd"}
    }
  }'
# Response: {"allowed": false, "policy_id": "...", "reason": "..."}
```

## Policy Rules Schema

- `effect`: `"allow"` or `"deny"`
- `match`: `{ "service": "stripe", "action_name": "charge" }` (supports `*` wildcard)
- `conditions`: `[{ "field": "metadata.amount", "operator": "gt", "value": 1000 }]`
  - Operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `contains`
