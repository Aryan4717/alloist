# Cursor Integration

Use Alloist with Cursor to enforce token checks on agent actions. This guide covers Cursor rules and pre-action hooks.

## Cursor Rules

Add a rule in `.cursor/rules/` to require token verification before high-risk actions:

**Example: `.cursor/rules/alloist-enforcement.mdc`**

```markdown
---
description: Enforce Alloist token checks on agent actions
globs: ["**/*.py", "**/*.js", "**/*.ts"]
---

# Alloist Token Enforcement

Before executing high-risk actions (e.g. `send_email`, `run_shell`, `stripe.charge`, `delete_file`):

1. **Verify the request includes a valid Alloist token** — The agent request must carry a JWT from the Alloist token service.
2. **Call the policy service** — Use `createEnforcement` (Node) or `create_enforcement` (Python) to check the token and action against policy.
3. **Block if denied** — If `enforcement.check()` returns `allowed: false`, do not execute the action. Return the `reason` and `evidence_id` to the user.

## High-risk actions (require token check)

- `send_email`, `gmail.send`
- `run_shell`, `execute_command`
- `stripe.charge`, `transfer_funds`
- `delete_file`, `delete_user`
- Any action that modifies external state or accesses sensitive data

## Implementation

- **Node**: `const { createEnforcement } = require('@alloist/enforcement');`
- **Python**: `from alloist_enforce import create_enforcement`
- **Ref SDK (verification only)**: `@alloist/ref-sdk-node` or `alloist-ref-sdk-py`
```

## Pre-action hook

For MCP or custom hooks, add a pre-action validator that:

1. Extracts the Alloist token from the request (header, env, or tool input).
2. Calls `enforcement.check(token, action_name, metadata)`.
3. Blocks execution if `allowed === false` and returns the denial reason.

```javascript
// Example pre-action hook (Node)
async function beforeExecute(action, input) {
  const token = input.alloist_token || process.env.ALLOIST_TOKEN;
  if (!token) throw new Error('Missing Alloist token');
  const result = await enforcement.check({ token, action });
  if (!result.allowed) throw new Error(`Blocked: ${result.reason}`);
}
```

## Admin UI

Create tokens and policies via the Alloist Admin UI:

```bash
cd apps/admin && npm run dev
```

- **Tokens**: Create tokens with scopes; revoke when needed.
- **Policies**: Define allow/deny rules per action and scope.
- **Evidence**: View and download signed evidence bundles for audits.

## References

- [Enforcement SDK (Node)](../../packages/enforcement)
- [Enforcement SDK (Python)](../../packages/enforcement_py)
- [Reference SDKs](../../packages/ref-sdk-node) — verification-only, no policy
- [LangChain integration](./langchain.md)
