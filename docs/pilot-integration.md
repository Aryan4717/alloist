# Pilot Integration Guide

Integrate Alloist with your AI agents. Set these environment variables (or use `.env`):

- `TOKEN_SERVICE_URL` – http://localhost:8000
- `POLICY_SERVICE_URL` – http://localhost:8001
- `TOKEN_SERVICE_API_KEY` – dev-api-key (or your key)
- `POLICY_SERVICE_API_KEY` – dev-api-key (or your key)

---

## LangChain Agents

Gate LangChain tool execution with `create_enforcement` (Python) or `createEnforcement` (Node). See [integrations/langchain.md](integrations/langchain.md) for full details.

**Python:** Wrap tools with `with_enforcement(action_name)` – pass `alloist_token` or `token` in tool input.

**Node:** Use `withEnforcement(actionName, fn)` – pass `token` or `alloist_token` in input.

---

## Python Agents

**Install:** `pip install -e packages/enforcement_py` or `pip install httpx` + path to enforcement_py.

```python
from alloist_enforce import create_enforcement

enforcement = create_enforcement(
    api_url="http://localhost:8000",
    api_key="dev-api-key",
    policy_service_url="http://localhost:8001",
    policy_service_api_key="dev-api-key",
    fail_closed=True,
    high_risk_actions=["send_email", "stripe.charge"],
)

result = enforcement.check(
    token="eyJ...",
    action_name="gmail.send",
    metadata={"to": "user@example.com"},
)

if not result["allowed"]:
    raise PermissionError(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
# Proceed with action
enforcement.close()
```

See [packages/enforcement_py/README.md](../packages/enforcement_py/README.md) for options (`fail_mode`, `fail_mode_per_action`).

---

## Node Agents

**Install:** `npm install @alloist/enforcement` or use `packages/enforcement`.

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

See [packages/enforcement/README.md](../packages/enforcement/README.md) for options (`failMode`, `failModePerAction`).
