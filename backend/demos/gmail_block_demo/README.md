# Gmail Block Demo

Demo agent that attempts to send email via Gmail (`gmail.send`). The Enforcement SDK intercepts the action and blocks it when a policy denies `gmail.send`. The blocked result includes an `evidence_id` for audit.

## Prerequisites

1. **Docker** – Token service and policy service must be running
2. **Python 3.10+** with pip

## Step 1: Start Services

From the repo root:

```bash
cd backend/token_service
docker compose up -d
```

This starts:
- Token service on http://localhost:8000
- Policy service on http://localhost:8001
- PostgreSQL

Wait for services to be healthy (about 10–15 seconds).

## Step 2: Install Dependencies

From the repo root:

```bash
pip install -e packages/enforcement_py
pip install httpx
```

Or from the demo directory:

```bash
cd backend/demos/gmail_block_demo
pip install -e ../../../packages/enforcement_py
pip install -r requirements.txt
```

## Step 3: Run the Demo

**Option A – Full flow (recommended)**

The CLI creates a token, creates a deny policy for `gmail.send`, runs the agent, and shows the blocked result:

```bash
cd backend/demos/gmail_block_demo
python run_demo.py
```

**Expected output:**

```
1. Creating token...
   Token created (id: <uuid>)
2. Creating policy (deny gmail.send)...
   Policy created
3. Running demo agent (attempts gmail.send)...
   Blocked: Block Gmail send (evidence_id: <uuid>)

Demo complete: Agent was blocked by policy (expected).
Evidence ID shown above proves the enforcement intercept.
```

**Option B – Manual run**

1. Create a token:
   ```bash
   curl -X POST http://localhost:8000/tokens \
     -H "X-API-Key: dev-api-key" \
     -H "Content-Type: application/json" \
     -d '{"subject":"demo","scopes":["email:send"],"ttl_seconds":3600}'
   ```
   Copy the `token` value from the response.

2. Create the policy:
   ```bash
   curl -X POST http://localhost:8001/policy \
     -H "X-API-Key: dev-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Block Gmail send",
       "description": "Deny gmail.send for demo",
       "rules": {
         "effect": "deny",
         "match": {"service": "gmail", "action_name": "send"},
         "conditions": []
       }
     }'
   ```

3. Run the agent with the token:
   ```bash
   python agent.py <token>
   ```

   Expected: `Blocked: Block Gmail send (evidence_id: <uuid>)`

## Step 4: Verify the Block

The `evidence_id` in the output is a UUID that uniquely identifies the enforcement decision. It can be used for:

- Audit logs
- Tracing blocked actions
- Compliance evidence

## Environment Variables

| Variable | Default | Description |
|---------|---------|-------------|
| TOKEN_SERVICE_URL | http://localhost:8000 | Token service base URL |
| TOKEN_SERVICE_API_KEY | (empty) | API key for token service |
| POLICY_SERVICE_URL | http://localhost:8001 | Policy service base URL |
| POLICY_SERVICE_API_KEY | dev-api-key | API key for policy service |

For local Docker, the default `dev-api-key` is used by both services.

## Flow Summary

1. Agent has a valid token with `email:send` scope
2. Agent attempts `gmail.send` to an external address
3. Enforcement SDK calls `check(token, "gmail.send", metadata)`
4. SDK validates token, then calls policy service `/policy/evaluate`
5. Policy service finds a deny rule for `gmail.send` and returns `allowed: false`
6. SDK returns blocked result with `evidence_id`
7. Agent prints the blocked message and exits with code 1
