# LangChain Integration

Use Alloist to gate LangChain tool execution. Before a tool runs, call `enforcement.check(token, action_name, metadata)` and block if denied.

## Node.js (with @alloist/enforcement)

Wrap tools with a pre-execution check using `createEnforcement`:

```javascript
const { createEnforcement } = require('@alloist/enforcement');
const { tool } = require('@langchain/core/tools');

const enforcement = createEnforcement({
  apiUrl: process.env.TOKEN_SERVICE_URL || 'http://localhost:8000',
  apiKey: process.env.TOKEN_SERVICE_API_KEY || '',
  failClosed: true,
  highRiskActions: ['send_email', 'run_shell', 'stripe_charge'],
});

function withEnforcement(actionName, fn) {
  return tool(async (input, runManager) => {
    const token = input.token ?? input.alloist_token;
    if (!token) throw new Error('Missing Alloist token');
    const result = await enforcement.check({
      token,
      action: { name: actionName, metadata: input },
    });
    if (!result.allowed) {
      throw new Error(`Blocked: ${result.reason} (evidence_id: ${result.evidence_id})`);
    }
    return fn(input, runManager);
  }, {
    name: actionName,
    description: '...',
    schema: YourInputSchema,
  });
}

// Example: guarded send_email tool
const sendEmailTool = withEnforcement('send_email', async (input) => {
  // ... actual send logic
  return { sent: true };
});
```

## Python (with alloist-enforce)

Use `create_enforcement` before `tool.invoke()`:

```python
from langchain_core.tools import tool
from alloist_enforce import create_enforcement

enforcement = create_enforcement(
    api_url=os.environ.get("TOKEN_SERVICE_URL", "http://localhost:8000"),
    api_key=os.environ.get("TOKEN_SERVICE_API_KEY", ""),
    policy_service_url=os.environ.get("POLICY_SERVICE_URL", "http://localhost:8001"),
    fail_closed=True,
    high_risk_actions=["send_email", "run_shell", "stripe.charge"],
)

def with_enforcement(action_name: str):
    def decorator(fn):
        @tool
        def wrapped(**kwargs):
            token = kwargs.pop("alloist_token", kwargs.pop("token", None))
            if not token:
                raise ValueError("Missing Alloist token")
            result = enforcement.check(token, action_name=action_name, metadata=kwargs)
            if not result["allowed"]:
                raise PermissionError(
                    f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})"
                )
            return fn(**kwargs)
        return wrapped
    return decorator

@with_enforcement("send_email")
def send_email(to: str, subject: str, body: str) -> dict:
    # ... actual send logic
    return {"sent": True}
```

## Verification-only (ref-sdk)

For minimal verification without policy or revocation push, use the reference SDKs:

- **Node**: `@alloist/ref-sdk-node` — `verifyToken(token, jwks)`, `verifyEvidenceBundle(bundle)`, `verifyRevocationPayload(payload, publicKey)`
- **Python**: `alloist-ref-sdk-py` — `verify_token()`, `verify_evidence_bundle()`, `verify_revocation_payload()`

See [packages/ref-sdk-node](../../packages/ref-sdk-node) and [packages/ref-sdk-py](../../packages/ref-sdk-py).
