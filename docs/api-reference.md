# API Reference

Base URLs: **Token Service** `http://localhost:8000` | **Policy Service** `http://localhost:8001`

Interactive docs: http://localhost:8000/docs and http://localhost:8001/docs

---

## Authentication

All endpoints except `GET /keys` require authentication. Use one of:

- **X-API-Key**: `dev-api-key`
- **Authorization**: `Bearer dev-api-key`

For multi-org setups, include **X-Org-Id** with the organization UUID. If omitted, the default org `00000000-0000-0000-0000-000000000001` is used.

---

## Token API (Token Service, port 8000)

### POST /tokens – Mint Token

Creates a new capability token (JWT) for an agent.

**Request:**

```bash
curl -X POST http://localhost:8000/tokens \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"subject":"demo-agent","scopes":["email:send","payments"],"ttl_seconds":3600}'
```

**Body:**

| Field        | Type     | Description                  |
|--------------|----------|------------------------------|
| `subject`    | string   | Agent or user identifier     |
| `scopes`     | string[] | Capability scopes            |
| `ttl_seconds`| number   | Token lifetime (1–31536000)  |

**Response:** `{ "token": "<jwt>", "token_id": "<uuid>", "expires_at": "<iso8601>" }`

---

### POST /tokens/revoke – Revoke Token

Invalidates a token. Broadcasts to WebSocket clients for real-time revocation. Admin role required.

**Request:**

```bash
curl -X POST http://localhost:8000/tokens/revoke \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"token_id":"<token_id from mint>"}'
```

**Body:** `{ "token_id": "<uuid>" }`

**Response:** `{ "success": true }`

---

### Other Token endpoints

| Endpoint              | Description                                  |
|-----------------------|----------------------------------------------|
| `POST /tokens/validate` | Verify JWT and DB status; returns valid, status, subject, scopes, jti |
| `GET /tokens`         | List tokens (optional: status, subject, limit, offset) |
| `GET /tokens/{token_id}` | Get token metadata (subject, scopes, issued_at, expires_at, status) |
| `GET /keys`           | JWKS for JWT verification (**no auth**)    |

---

## Policy API (Policy Service, port 8001)

### POST /policy/evaluate – Evaluate Policy

Checks whether an action is allowed for a given token.

**Request:**

```bash
curl -X POST http://localhost:8001/policy/evaluate \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "token_id": "<token_id from mint>",
    "action": {
      "service": "gmail",
      "name": "send",
      "metadata": {}
    }
  }'
```

**Body:**

| Field      | Type   | Description                          |
|------------|--------|--------------------------------------|
| `token_id` | uuid   | Token ID (from mint response)        |
| `action`   | object | `{ service, name, metadata }`       |

**Response:** `{ "allowed": boolean, "policy_id"?: uuid, "reason"?: string, "consent_request_id"?: string }`

- `allowed: true` – Action is allowed; agent may proceed.
- `allowed: false` – Action is denied; `reason` explains why.
- `consent_request_id` – Action requires human consent; call `POST /consent/decision` with the decision, then re-evaluate.

**Enforcement header:** Send `X-Request-Type: enforcement` when the request is from an SDK enforcement check (for usage metrics).

---

### POST /policy – Create Policy

Creates a policy with allow/deny/require_consent rules.

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

**Body – deny stripe.charge when amount > 1000:**

```json
{
  "name": "Block large Stripe charges",
  "rules": {
    "effect": "deny",
    "match": { "service": "stripe", "action_name": "charge" },
    "conditions": [
      { "field": "metadata.amount", "operator": "gt", "value": 1000 }
    ]
  }
}
```

**Body – require consent for stripe.charge:**

```json
{
  "name": "Require consent for stripe.charge",
  "rules": {
    "effect": "require_consent",
    "match": { "service": "stripe", "action_name": "charge" },
    "conditions": []
  }
}
```

`match.service` and `match.action_name` support `*` for wildcard. See [PHASE1_MVP.md](../PHASE1_MVP.md) for more examples.

---

### GET /policy – List Policies

Returns all policies for the org.

---

## Consent System

When a policy has `effect: "require_consent"`, the evaluate endpoint returns `consent_request_id` instead of allow/deny. A human must approve or deny before the agent can proceed.

### Browser extension flow

1. Policy with `effect: "require_consent"` matches the action.
2. `POST /policy/evaluate` returns `consent_request_id`; backend broadcasts to WebSocket at `/consent/ws`.
3. Extension receives the request and shows a popup (agent name, action, metadata, risk level).
4. User clicks Approve or Deny.
5. Extension calls `POST /consent/decision` with `{ request_id, decision: "approve" | "deny" }`.
6. Agent (or SDK) re-evaluates; policy service resolves the pending request and returns allow or deny.

See [PHASE6_README.md](../PHASE6_README.md) and [apps/browser-extension/TESTING_GUIDE.md](../apps/browser-extension/TESTING_GUIDE.md).

### Mobile consent flow

1. App fetches pending requests: `GET /consent/pending`.
2. User taps Approve or Deny; app calls `POST /consent/decision`.
3. For push notifications: app registers with `POST /consent/register-device` (Expo push token).

### Consent endpoints

| Endpoint                   | Description                                      |
|----------------------------|--------------------------------------------------|
| `GET /consent/pending`     | List pending consent requests for the org       |
| `POST /consent/decision`   | Submit approve or deny. Body: `{ request_id, decision: "approve" \| "deny" }` |
| `POST /consent/register-device` | Register device for push. Body: `{ expo_push_token, device_id? }` |
| `WebSocket /consent/ws`    | Real-time consent requests (browser extension)  |

---

## SDK Usage Examples

The enforcement SDKs wrap agent actions and check token + policy before execution.

### Python (alloist-enforce)

**Install:** `pip install -e packages/enforcement_py` or `pip install alloist-enforce`

```python
from alloist_enforce import create_enforcement

enforcement = create_enforcement(
    api_url="http://localhost:8000",
    api_key="dev-api-key",
    policy_service_url="http://localhost:8001",
    policy_service_api_key="dev-api-key",
    fail_mode="fail_closed",
    high_risk_actions=["send_email", "stripe.charge"],
)

result = enforcement.check(
    token="eyJ...",
    action_name="stripe.charge",
    metadata={"amount": 1500},
)

if not result["allowed"]:
    raise PermissionError(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
# Proceed with action
enforcement.close()
```

**Options:** `fail_mode` (fail_closed, soft_fail, fail_open), `fail_mode_per_action`, `on_log`. See [packages/enforcement_py/README.md](../packages/enforcement_py/README.md).

### Node.js (@alloist/enforcement)

**Install:** `npm install @alloist/enforcement` or use `packages/enforcement`

```javascript
const { createEnforcement } = require('@alloist/enforcement');

const enforcement = createEnforcement({
  apiUrl: 'http://localhost:8000',
  apiKey: 'dev-api-key',
  failClosed: true,
  highRiskActions: ['send_email', 'stripe_charge'],
});

const result = await enforcement.check({
  token: 'eyJ...',
  action: { name: 'send_email', service: 'email', metadata: { to: 'user@example.com' } },
});

if (!result.allowed) {
  throw new Error(`Blocked: ${result.reason} (evidence_id: ${result.evidence_id})`);
}
// Proceed with action
enforcement.close();
```

**Action format:** Use `action_name` with dot notation (e.g. `stripe.charge`) or `action: { name, service, metadata }`. See [packages/enforcement/README.md](../packages/enforcement/README.md).

### Fail modes

When the token or policy backend is unreachable:

- **fail_closed** – Block the action (safe default for high-risk).
- **soft_fail** – Allow but create high-severity evidence.
- **fail_open** – Allow without special audit.

Use `fail_mode_per_action` to override per action.

---

## Evidence Bundles

When an action is denied, the enforcement flow creates an evidence record. Export it for auditors.

### Format

The evidence bundle (see [spec/SPEC.md](../spec/SPEC.md) section 2) includes:

| Field               | Type   | Description                              |
|---------------------|--------|------------------------------------------|
| `evidence_id`       | string | Unique evidence record ID                 |
| `action_name`       | string | e.g. `gmail.send`, `stripe.charge`        |
| `token_snapshot`    | object | Token claims at evaluation time           |
| `timestamp`         | string | ISO 8601                                 |
| `input_hash`        | string | SHA256 of action + token + metadata       |
| `policy_id`         | string | Policy that matched (if any)              |
| `result`            | string | `allow` or `deny`                        |
| `runtime_metadata`  | object | Additional context                       |
| `public_key`        | string | Base64 Ed25519 public key                 |
| `runtime_signature` | string | Base64 Ed25519 signature                  |

The payload is canonical JSON (sorted keys); the signature is over the bundle excluding `runtime_signature`.

### Export

```bash
curl -X POST http://localhost:8001/evidence/export \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"evidence_id":"<evidence_id from blocked action>"}'
```

**Response:** `{ "bundle": {...}, "signature": "<base64>", "public_key": "<base64>" }`

### Verification

Use the reference SDKs to verify evidence signatures:

**Python:**

```python
from alloist_ref_sdk import verify_evidence_bundle
ok = verify_evidence_bundle(bundle)
```

**Node:**

```javascript
const { verifyEvidenceBundle } = require('@alloist/ref-sdk-node');
const ok = verifyEvidenceBundle(bundle);
```

### Other evidence endpoints

| Endpoint               | Description                          |
|------------------------|--------------------------------------|
| `GET /evidence`        | List evidence (result, action_name, since, limit, offset) |
| `POST /evidence/create`| Create evidence (used by SDK)        |
| `GET /evidence/keys`   | Public key for verification          |

---

## Related Documentation

- [Getting Started](getting-started.md) – Run services, configure env
- [Architecture](architecture.md) – How Alloist works
- [PHASE1_MVP.md](../PHASE1_MVP.md) – Full API reference, Postman flow, demos
- [docs/integrations/langchain.md](integrations/langchain.md) – LangChain tool wrapping
