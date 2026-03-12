# Alloist Phase 9

## In Plain English (One-Read Summary)

Phase 9 delivers **developer-friendly SDKs and agent examples** for quick integration:

**9.1 Python SDK** – A simple Python SDK (`alloist`) with `init()` and `enforce()`. One line of code gates any action. Call `enforce(action="gmail.send", metadata={...})` before sending email; if policy denies, `AlloistPolicyDeniedError` is raised and your action never runs.

**9.2 Node SDK** – A Node.js SDK (`@alloist/sdk`) with the same API. `init()` and `enforce()` work identically. Async by default. Use with TypeScript or JavaScript to gate agent actions in Node runtimes.

**9.3 Agent Examples** – Minimal example agents (email, booking, github) that demonstrate `enforce()` in practice. Each agent calls `enforce()` before performing a sensitive action. Run them with a capability token to see Alloist allow or block in real time.

---

## What Phase 9 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **9.1** | `features/hdk/pythondave` | Python developer SDK: init, enforce, AlloistPolicyDeniedError |
| **9.2** | `features/sdk-node-dev` | Node.js developer SDK: init, enforce, TypeScript types |
| **9.3** | `features/agent-example` | Agent examples: email_agent, booking_agent, github_agent |

---

## 9.1 Python SDK

Simple policy enforcement for AI agents. Gate actions with one line of code.

### In plain English

- **init(api_key=...)** – Initialize the SDK with your capability token (from minting).
- **enforce(action, metadata)** – Check if the action is allowed. Returns on allow; raises `AlloistPolicyDeniedError` on deny.
- **Policy service URL** – Defaults to `http://localhost:8001`. Override via `init(policy_service_url=...)`.

### Location

**Package**: `packages/sdk-python/`

### Install

```bash
pip install -e packages/sdk-python
```

### Usage

```python
from alloist import init, enforce, AlloistPolicyDeniedError

init(api_key=os.environ["ALLOIST_TOKEN"])

try:
    enforce(action="gmail.send", metadata={"to": "user@gmail.com"})
    send_email(to="user@gmail.com", body="Hello")
except AlloistPolicyDeniedError:
    print("Cannot send email - policy denied")
```

### Requirements

- Python 3.10+
- Alloist policy service running with `/enforce` endpoint

---

## 9.2 Node SDK

Node.js SDK for Alloist policy enforcement. Gate AI agent actions with one line of code.

### In plain English

- **init({ apiKey })** – Initialize the SDK with your capability token.
- **enforce(action, metadata)** – Async check. Returns on allow; throws on deny.
- **TypeScript** – Full type definitions for `InitOptions`, `EnforceResponse`.

### Location

**Package**: `packages/sdk-node/`

### Install

```bash
npm install @alloist/sdk
```

Or from the monorepo:

```bash
npm install -e packages/sdk-node
```

### Usage

```typescript
import { init, enforce } from "@alloist/sdk";

init({ apiKey: process.env.ALLOIST_TOKEN });

try {
  await enforce("gmail.send", { to: "user@gmail.com" });
  await sendEmail({ to: "user@gmail.com", body: "Hello" });
} catch (err) {
  console.error("Cannot send email:", err.message);
}
```

### Requirements

- Node.js 18+
- Alloist policy service running with `/enforce` endpoint

---

## 9.3 Agent Examples

Minimal AI agents that call `enforce()` before performing actions. If Alloist policy denies the request, `AlloistPolicyDeniedError` is raised and the action never executes.

### In plain English

- **email_agent** – Sends emails. Enforces `gmail.send` with recipient metadata. Default policies deny gmail.send.
- **booking_agent** – Creates bookings. Enforces `booking.create` with price metadata. Add policy to deny when price > 1000.
- **github_agent** – Pushes code. Enforces `github.push` with branch metadata.

Each example shows the pattern: call `enforce()` before the action, catch `AlloistPolicyDeniedError` for denied cases.

### Location

**Directory**: `examples/`

| Agent | Path | Action | Description |
|-------|------|--------|-------------|
| Email | `examples/email_agent/` | `gmail.send` | Recipient metadata |
| Booking | `examples/booking_agent/` | `booking.create` | Price metadata |
| GitHub | `examples/github_agent/` | `github.push` | Branch metadata |

### Prerequisites

1. Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
2. Capability token minted (`python examples/create_token.py`)
3. Policies applied (`python examples/apply_policies.py`)
4. Alloist SDK: `pip install -e packages/sdk-python`

### Run

```bash
# From repo root
ALLOIST_TOKEN=your_token python examples/email_agent/agent.py user@example.com
ALLOIST_TOKEN=your_token python examples/booking_agent/agent.py user 50.0
ALLOIST_TOKEN=your_token python examples/github_agent/agent.py main
```

### Environment

Set or export: `TOKEN_SERVICE_URL`, `TOKEN_SERVICE_API_KEY`, `POLICY_SERVICE_URL`, `POLICY_SERVICE_API_KEY` (defaults work with pilot `.env`).

---

## Full Testing Checklist (Phase 9)

### 9.1 Python SDK

- [ ] `python -c "from alloist import init, enforce; init(api_key='test'); print('ok')"` runs
- [ ] `enforce(action="gmail.send", metadata={"to": "x"})` raises `AlloistPolicyDeniedError` when policy denies
- [ ] `enforce()` returns when policy allows

### 9.2 Node SDK

- [ ] `import { init, enforce } from "@alloist/sdk"` works
- [ ] `await enforce("gmail.send", { to: "x" })` throws when policy denies
- [ ] `enforce()` resolves when policy allows

### 9.3 Agent Examples

- [ ] `examples/email_agent/agent.py` runs; policy denies gmail.send; prints "Blocked"
- [ ] `examples/booking_agent/agent.py` runs; policy allows or denies based on price
- [ ] `examples/github_agent/agent.py` runs; policy allows or denies based on branch

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `features/hdk/pythondave` | Python developer SDK: init, enforce, AlloistPolicyDeniedError |
| `features/sdk-node-dev` | Node.js developer SDK: init, enforce, TypeScript types |
| `features/agent-example` | Agent examples: email_agent, booking_agent, github_agent |

---

## Consistency with Phase 1–8

Phase 9 follows the same structure:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification
- **Branch summary** – Quick reference

Phase 9 is about **developer experience**: simple SDKs that developers can drop into their agents in minutes, with example agents that show the pattern in action.
