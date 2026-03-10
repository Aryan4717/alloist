# @alloist/enforcement

Tiny Node.js SDK for token and policy enforcement with offline caching, TTL checks, and real-time revocation via WebSocket.

## Installation

```bash
npm install @alloist/enforcement
```

## Usage

```javascript
const { createEnforcement } = require('@alloist/enforcement');

const enforcement = createEnforcement({
  apiUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',
  failClosed: true,
  highRiskActions: ['send_email', 'delete_user', 'transfer_funds'],
});

const result = await enforcement.check({
  token: 'eyJ...',
  action: { name: 'send_email', service: 'email', metadata: { to: 'user@example.com' } },
});

if (!result.allowed) {
  throw new Error(`Blocked: ${result.reason} (evidence_id: ${result.evidence_id})`);
}
// Proceed with action
```

## API

### `createEnforcement(options)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiUrl` | string | `'http://localhost:8000'` | Token service base URL |
| `apiKey` | string | `''` | API key for validation endpoint |
| `failClosed` | boolean | `false` | (Legacy) Block high-risk actions when backend unreachable |
| `highRiskActions` | string[] | `['send_email', 'delete_user', 'transfer_funds']` | (Legacy) Actions to block when failClosed |
| `failMode` | string | `'fail_open'` | Default when backend unreachable: `fail_closed`, `soft_fail`, or `fail_open` |
| `failModePerAction` | object | null | Per-action override, e.g. `{ send_email: 'fail_closed', read_logs: 'soft_fail' }` |
| `onLog` | function | null | Callback for check events `{ evidence_id, action, result }` |
| `jwksOverride` | object | null | For testing: pass `{ keys: [...] }` to bypass JWKS fetch |

### `enforcement.check({ token, action })`

Returns `Promise<{ allowed: boolean, reason?: string, evidence_id?: string }>`.

- **token**: JWT string
- **action**: `{ name: string, service?: string, metadata?: object }`

## Behavior

1. **Local validation**: Verifies JWT signature (Ed25519) and TTL via JWKS from `GET /keys`.
2. **Revocation cache**: In-memory set of revoked token IDs (updated via WebSocket).
3. **Remote fallback**: If not cached, calls `POST /tokens/validate` to check status.
4. **Policy**: Maps `action.name` to required scope (e.g. `send_email` → `email:send`).
5. **Evidence**: Each check gets a unique `evidence_id` (UUID).
6. **Fail modes** (when token backend unreachable):
   - `fail_closed`: Block action with `fail_closed_backend_unreachable`
   - `soft_fail`: Allow and log `degraded_mode: 'soft_fail'` via `onLog`
   - `fail_open`: Allow without special audit
   - Use `failModePerAction` for per-action overrides; legacy `failClosed` + `highRiskActions` still supported

## Backend Requirements

- `GET /keys` — JWKS (public keys)
- `POST /tokens/validate` — `{ token }` → `{ valid, status, subject, scopes, jti }`
- `WS /ws/revocations` — Push `{ token_id, event: "revoked" }` on revocation

## Example

See [examples/send_email_demo.js](examples/send_email_demo.js).

```bash
TOKEN_SERVICE_API_KEY=your-key node examples/send_email_demo.js <token>
```

## Tests

```bash
npm test
```
