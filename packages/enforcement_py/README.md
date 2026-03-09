# cognara-enforce

Python SDK for token and policy enforcement with offline caching, TTL checks, and real-time revocation via WebSocket. Mirrors the Node.js `@cognara/enforcement` SDK.

## Installation

```bash
pip install cognara-enforce
```

Or from source:

```bash
cd packages/enforcement_py && pip install -e .
```

## Usage

```python
from cognara_enforce import create_enforcement

enforcement = create_enforcement(
    api_url="http://localhost:8000",
    api_key="your-api-key",
    fail_closed=True,
    high_risk_actions=["send_email", "delete_user", "transfer_funds"],
)

result = enforcement.check(
    token="eyJ...",
    action_name="send_email",
    metadata={"to": "user@example.com"},
)

if not result["allowed"]:
    raise PermissionError(f"Blocked: {result['reason']} (evidence_id: {result['evidence_id']})")
# Proceed with action
```

## API

### `create_enforcement(...)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_url` | str | `"http://localhost:8000"` | Token service base URL |
| `api_key` | str | `""` | API key for validation endpoint |
| `fail_closed` | bool | `False` | (Legacy) Block high-risk actions when backend unreachable |
| `high_risk_actions` | list[str] | `["send_email", "delete_user", "transfer_funds"]` | (Legacy) Actions to block when fail_closed |
| `fail_mode` | str | `"fail_open"` | Default when backend unreachable: `fail_closed`, `soft_fail`, or `fail_open` |
| `fail_mode_per_action` | dict[str, str] | None | Per-action override, e.g. `{"send_email": "fail_closed", "read_logs": "soft_fail"}` |
| `on_log` | callable | None | Callback for check events `{evidence_id, action, result}` |
| `jwks_override` | dict | None | For testing: pass `{keys: [...]}` to bypass JWKS fetch |

### `enforcement.check(token, action_name, metadata=None)`

Returns `dict` with `allowed: bool`, `reason?: str`, `evidence_id: str`.

## Behavior

1. **Local validation**: Verifies JWT signature (Ed25519) and TTL via JWKS from `GET /keys`.
2. **Revocation cache**: In-memory set of revoked token IDs (updated via WebSocket).
3. **Remote fallback**: If not cached, calls `POST /tokens/validate` to check status.
4. **Policy**: Maps `action_name` to required scope (e.g. `send_email` -> `email:send`).
5. **Evidence**: Each check gets a unique `evidence_id` (UUID).
6. **Fail modes** (when token or policy backend unreachable):
   - `fail_closed`: Block action with `fail_closed_backend_unreachable`
   - `soft_fail`: Allow but create high-severity evidence (`severity: "high"`, `degraded_mode: "soft_fail"`)
   - `fail_open`: Allow without special audit
   - Use `fail_mode_per_action` for per-action overrides; legacy `fail_closed` + `high_risk_actions` still supported

## Backend Requirements

- `GET /keys` — JWKS (public keys)
- `POST /tokens/validate` — `{token}` -> `{valid, status, subject, scopes, jti}`
- `WS /ws/revocations` — Push `{token_id, event: "revoked"}` on revocation

## Example

```bash
TOKEN_SERVICE_API_KEY=your-key python examples/dummy_agent.py <token>
```

## Tests

```bash
pytest tests/ -v
```
