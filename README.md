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
├── spec/                   # ACT-lite spec (alloist/spec)
├── apps/
│   ├── admin/              # Next.js admin UI (Phase 3)
│   ├── browser-extension/  # Chrome extension for consent (Phase 6)
│   └── mobile-consent/     # React Native app for consent (Phase 6)
├── backend/
│   ├── token_service/       # Mints tokens, revocation, JWKS (port 8000)
│   ├── policy_service/      # Policy evaluation, evidence export (port 8001)
│   └── demos/
│       ├── gmail_block_demo/    # Blocks gmail.send
│       ├── stripe_block_demo/   # Blocks stripe.charge > $1000
│       └── yc_demo/             # Full flow: block, revoke, export+verify
├── packages/
│   ├── enforcement_py/      # Python SDK for enforcement
│   ├── enforcement/        # Node.js SDK
│   ├── ref-sdk-node/       # Minimal reference SDK (verification only)
│   ├── ref-sdk-py/        # Minimal reference SDK (verification only)
│   └── conformance/       # ACT-lite conformance test harness
├── docs/
│   └── integrations/      # LangChain, Cursor integration guides
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

## Phase 4

Phase 4 makes Alloist open-source and interoperable: ACT-lite spec, reference SDKs, and conformance tests.

**See [PHASE4_README.md](PHASE4_README.md) for:**
- 4.1 ACT-lite specification (token, evidence, revocation; JSON schemas; conformance list)
- 4.2 Reference SDKs (ref-sdk-node, ref-sdk-py) and conformance harness
- Integration docs (LangChain, Cursor)
- Full testing checklist

## Phase 5

Phase 5 makes Alloist team-ready and production-oriented: org RBAC, audit retention, SSO, and billing foundation.

**See [PHASE5_README.md](PHASE5_README.md) for:**
- 5.1 Organization RBAC (admin/developer/viewer roles)
- 5.2 Audit retention (retention_days, auto-cleanup, list/export)
- 5.3 SSO (OAuth Google/GitHub, JWT sessions, admin login)
- 5.4 Billing stub (subscriptions, usage limits, Stripe placeholder)
- Full testing checklist

## Phase 6

Phase 6 adds consent interfaces for approving AI agent actions in real time: a Chrome extension and a React Native mobile app.

**See [PHASE6_README.md](PHASE6_README.md) for:**
- 6.1 Browser extension (WebSocket, popup, Approve/Deny)
- 6.2 Mobile app (pending list, push notifications, device registration)
- Full testing checklist

## Phase 7

Phase 7 adds logging, monitoring, and secure secret management for production readiness.

**See [PHASE7_README.md](PHASE7_README.md) for:**
- 7.1 Structured JSON logging (secret redaction, exception sanitization)
- 7.2 Prometheus metrics, health/ready endpoints
- 7.3 Secret loader (env/AWS/Vault cascade, rotation, startup validation)
- Full testing checklist

## Phase 8

Phase 8 adds documentation, demo scripts, and the pilot kit for easy adoption and evaluation.

**See [PHASE8_README.md](PHASE8_README.md) for:**
- 8.1 Developer docs (architecture, getting-started, api-reference)
- 8.2 Demo scripts (gmail, stripe, revoke, consent)
- 8.3 Pilot kit (docker-compose, start.sh, examples, integration guides)
- Full testing checklist

## ACT-lite Spec (alloist/spec)

The [spec/](spec/) directory contains the **Agent Capability Token (ACT-lite)** specification: token fields, evidence format, revocation semantics, key rotation, and verification steps. Includes JSON schemas, conformance tests, security recommendations, and examples. May be published as **alloist/spec**.

## Reference SDKs & Conformance

- **[ref-sdk-node](packages/ref-sdk-node)** — Minimal Node.js verification (token, evidence, revocation). No policy, no WebSocket.
- **[ref-sdk-py](packages/ref-sdk-py)** — Minimal Python verification (token, evidence, revocation). No policy, no WebSocket.
- **[Conformance harness](packages/conformance)** — Automated tests for token (1–5), evidence (6–9), revocation (10–12), and revoke propagation.

Run conformance tests:

```bash
make conformance
```

Or:

```bash
cd packages/conformance && npm install && npm run generate && npm test
```

## Pilot Deployment

Get a working Alloist environment in minutes:

```bash
cp .env.example .env
./scripts/start.sh
python examples/create_token.py
python examples/apply_policies.py
```

See [docs/pilot.md](docs/pilot.md) for details and [docs/pilot-integration.md](docs/pilot-integration.md) for LangChain, Python, and Node integration.

## Developer Documentation

- **[Architecture](docs/architecture.md)** — What Alloist does, architecture summary, key flows
- **[Getting Started](docs/getting-started.md)** — Docker Compose, environment variables, running services
- **[API Reference](docs/api-reference.md)** — Token API, Policy API, consent, SDK usage, evidence bundles

## Integration Guides

- **[LangChain](docs/integrations/langchain.md)** — Wrap tools with `createEnforcement` before execution.
- **[Cursor](docs/integrations/cursor.md)** — Cursor rules and pre-action hooks for token verification.





