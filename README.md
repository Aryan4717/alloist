# Alloist

AI permission layer for the Internet. Control what AI agents can do via capability tokens and policy enforcement.

## Overview

Alloist gates AI agent actions (e.g., send email, charge payment) using:

1. **Token Service** – Mints signed capability tokens (JWTs) for agents
2. **Policy Service** – Evaluates actions against JSON policies (allow/deny)
3. **Enforcement SDK** – Wraps agent actions and checks policy before execution
4. **Demos** – Show agents being blocked when policies deny actions

## Project Structure

```
alloist/
├── apps/
│   └── admin/              # Next.js admin UI (Phase 3)
├── backend/
│   ├── token_service/       # Mints tokens, revocation, JWKS (port 8000)
│   ├── policy_service/      # Policy evaluation, evidence export (port 8001)
│   └── demos/
│       ├── gmail_block_demo/    # Blocks gmail.send
│       ├── stripe_block_demo/   # Blocks stripe.charge > $1000
│       └── yc_demo/             # Full flow: block, revoke, export+verify
├── packages/
│   ├── enforcement_py/      # Python SDK for enforcement
│   └── enforcement/         # Node.js SDK
```

## Phase 1 MVP

Phase 1 delivers a working permission layer with token minting, policy evaluation, enforcement SDK, and evidence export.

**See [PHASE1_MVP.md](PHASE1_MVP.md) for:**
- Quick start (Docker, signing key, demos)
- Running tests
- Full API reference and Postman testing guide
- Environment variables
- Database connection details

## Phase 2

Phase 2 adds fail-closed modes, revocation push (Redis), and scale/perf testing.

**See [PHASE2_README.md](PHASE2_README.md) for:**
- 2.1 Fail-closed modes & offline resilience
- 2.2 Revocation push system (Redis pub/sub)
- 2.3 Scale & perf benchmarking
- Full testing checklist

## Phase 3

Phase 3 adds a Next.js admin console for policies, tokens, and evidence.

**Admin UI** (`apps/admin/`):
- Tokens list (create/revoke)
- Policies list (create/edit/delete) with template library
- Live Actions (enforcement events stream)
- Evidence exports (download signed bundles)
- Quickstart overlay (5-minute demo guide)

```bash
cd apps/admin && npm run dev
```
