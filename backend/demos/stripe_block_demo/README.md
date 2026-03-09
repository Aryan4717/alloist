# Stripe Block Demo

Demo agent that attempts a Stripe charge (`stripe.charge`). The Enforcement SDK intercepts the action and blocks it when a policy denies (e.g., amount > $1000). The blocked result includes an `evidence_id` for audit, and a script exports a signed evidence bundle.

## Prerequisites

1. **Docker** – Token service and policy service must be running
2. **Python 3.10+** with pip

## Step 1: Start Services

From the repo root:

```bash
cd backend/token_service
docker compose up -d
```

This starts token service (8000), policy service (8001), and PostgreSQL.

## Step 2: Install Dependencies

```bash
pip install -e packages/enforcement_py
pip install httpx
```

Or from the demo directory:

```bash
cd backend/demos/stripe_block_demo
pip install -e ../../../packages/enforcement_py
pip install -r requirements.txt
```

## Step 3: Run the Demo

**Full flow (recommended):**

```bash
cd backend/demos/stripe_block_demo
python run_demo.py
```

**Expected output:**

```
1. Creating token...
   Token created (id: <uuid>)
2. Creating policy (deny stripe.charge amount > 1000)...
   Policy created
3. Running demo agent (attempts stripe.charge $1500)...
   Blocked: Block large Stripe charges: metadata.amount 1500 exceeds threshold 1000 (evidence_id: <uuid>)

Demo complete: Agent was blocked by policy (expected).
Evidence ID shown above proves the enforcement intercept.
Evidence bundle exported to stripe_block_evidence.json
```

## Step 4: Sample Policies

**Policy 1: Deny charges above $1000** (used by demo)

```json
{
  "effect": "deny",
  "match": { "service": "stripe", "action_name": "charge" },
  "conditions": [{ "field": "metadata.amount", "operator": "gt", "value": 1000 }]
}
```

**Policy 2: Require allow_payment scope**

Requires `allow_payment` scope for stripe.charge; otherwise blocks:

```json
{
  "effect": "deny",
  "match": { "service": "stripe", "action_name": "charge" },
  "conditions": [{ "field": "token.scopes", "operator": "not_contains", "value": "allow_payment" }]
}
```

Create via `POST http://localhost:8001/policy` with the appropriate rules.

## Step 5: Export Evidence Bundle

```bash
python export_evidence.py <evidence_id> --reason "Block large Stripe charges" --output evidence.json
```

The bundle includes evidence_id, timestamp, action, result, reason, and a placeholder for signature.

## Manual Run

1. Create token: `POST /tokens` with `{"subject":"demo","scopes":["payments"],"ttl_seconds":3600}`
2. Create policy: `POST /policy` with the deny amount > 1000 rules
3. Run agent: `python agent.py <token> 1500`

## Environment Variables

| Variable | Default | Description |
|---------|---------|-------------|
| TOKEN_SERVICE_URL | http://localhost:8000 | Token service base URL |
| TOKEN_SERVICE_API_KEY | (empty) | API key for token service |
| POLICY_SERVICE_URL | http://localhost:8001 | Policy service base URL |
| POLICY_SERVICE_API_KEY | dev-api-key | API key for policy service |
