# Alloist Phase 8

## In Plain English (One-Read Summary)

Phase 8 makes Alloist **easy to adopt and evaluate**:

**8.1 Docs** – Developer documentation that covers architecture, quick start, and full API reference. New integrators learn what Alloist does, how to run it with Docker Compose, and how every endpoint works. No guesswork.

**8.2 Demo Scripts** – Standalone scripts that simulate AI agent actions and show enforcement in action: Gmail send, Stripe charge, token revocation, and consent flow. Each prints action, policy result, and evidence_id. Run them to see Alloist blocking or allowing in real time.

**8.3 Pilot Kit** – A turnkey setup to get Alloist running in minutes: root `docker-compose.yml`, `.env.example`, `scripts/start.sh`, example policies, token creation script, and integration guides. Copy, start, and integrate with LangChain, Python, or Node.

---

## What Phase 8 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **8.1** | `feature/docs` | Developer docs: architecture, getting-started, api-reference |
| **8.2** | `feature/demo-scripts` | Standalone demos: gmail, stripe, revoke, consent |
| **8.3** | `feature/pilot` | Pilot kit: docker-compose, start.sh, examples, pilot docs |

---

## 8.1 Docs

Developer documentation for architecture, quick start, and API reference.

### In plain English

- **Architecture** (`docs/architecture.md`) – What Alloist does, architecture summary (Token Service, Policy Service, SDKs, consent, evidence), and key flows (mint token, policy check, consent, revocation).
- **Getting Started** (`docs/getting-started.md`) – Run Docker Compose, configure environment variables, create signing key, run services locally.
- **API Reference** (`docs/api-reference.md`) – Token API (mint, revoke, JWKS), Policy API (evaluate, evidence, consent), authentication, SDK usage, evidence bundles.

### Location

| Doc | Path | Description |
|-----|------|-------------|
| Architecture | `docs/architecture.md` | Overview, components, flows |
| Getting Started | `docs/getting-started.md` | Docker Compose, env vars, local setup |
| API Reference | `docs/api-reference.md` | Endpoints, request/response formats |
| Pilot | `docs/pilot.md` | Quick start for evaluation |
| Pilot Integration | `docs/pilot-integration.md` | LangChain, Python, Node integration |

### Usage

Read in order for newcomers:

1. **[Architecture](docs/architecture.md)** – Understand what Alloist does
2. **[Getting Started](docs/getting-started.md)** – Run services
3. **[API Reference](docs/api-reference.md)** – Integrate with your agent
4. **[Pilot Integration](docs/pilot-integration.md)** – Wrap tools with enforcement

---

## 8.2 Demo Scripts

Standalone demo scripts that simulate AI agent actions and demonstrate enforcement behavior.

### In plain English

- **gmail_demo.py** – Simulates Gmail send. Policy denies `gmail.send`. Shows block + evidence.
- **stripe_demo.py** – Simulates Stripe charge. Policy denies `stripe.charge` when amount > 1000.
- **revoke_demo.py** – Token lifecycle: allow → revoke → block.
- **consent_demo.py** – Consent flow: policy requires consent, simulates user approval.

Each demo prints: **action**, **policy result**, **evidence_id**.

### Location

**Directory**: `demos/`

| Script | Description |
|--------|-------------|
| `gmail_demo.py` | Gmail send – policy denies gmail.send |
| `stripe_demo.py` | Stripe payment – deny stripe.charge > $1000 |
| `revoke_demo.py` | Token revocation – allow, revoke, then block |
| `consent_demo.py` | Consent flow – require_consent, simulate approval |

### Prerequisites

1. Start services:
   ```bash
   cd backend/token_service
   docker compose up -d
   ```

2. Create signing key (first run only):
   ```bash
   docker compose exec token_service python -m app.cli.rotate_key
   ```

3. Install dependencies (from repo root):
   ```bash
   pip install -r demos/requirements.txt
   ```

### Run

```bash
# From repo root
python demos/gmail_demo.py
python demos/stripe_demo.py
python demos/revoke_demo.py
python demos/consent_demo.py
```

---

## 8.3 Pilot Kit

Turnkey setup to get Alloist running in minutes for evaluation and development.

### In plain English

- **docker-compose.yml** (root) – Single command starts PostgreSQL, Redis, Token Service, Policy Service.
- **.env.example** – Template with required env vars. Copy to `.env`.
- **scripts/start.sh** – One script: copy env, run compose, create signing key when needed.
- **examples/** – `policies.json`, `create_token.py`, `apply_policies.py` to bootstrap a working setup.
- **Pilot docs** – `docs/pilot.md` (quick start), `docs/pilot-integration.md` (LangChain, Python, Node).

### Location

| File | Description |
|------|-------------|
| `docker-compose.yml` | Root compose for all services |
| `.env.example` | Env template |
| `scripts/start.sh` | Start script |
| `examples/policies.json` | Example policies |
| `examples/create_token.py` | Create capability token |
| `examples/apply_policies.py` | Apply policies to org |
| `docs/pilot.md` | Pilot quick start |
| `docs/pilot-integration.md` | Integration guides |

### Quick Start

```bash
cp .env.example .env
./scripts/start.sh
python examples/create_token.py
python examples/apply_policies.py
```

### Verify

- Token Service: http://localhost:8000/docs
- Policy Service: http://localhost:8001/docs
- JWKS: http://localhost:8000/keys

---

## Full Testing Checklist (Phase 8)

### 8.1 Docs

- [ ] `docs/architecture.md` exists and describes Token Service, Policy Service, SDKs, consent, evidence
- [ ] `docs/getting-started.md` has Docker Compose and env var instructions
- [ ] `docs/api-reference.md` documents Token API, Policy API, consent, SDK usage
- [ ] Docs are linked from root README under "Developer Documentation"

### 8.2 Demo Scripts

- [ ] `demos/gmail_demo.py` runs; policy denies gmail.send; prints evidence_id
- [ ] `demos/stripe_demo.py` runs; policy denies stripe.charge > $1000
- [ ] `demos/revoke_demo.py` runs; allow → revoke → block flow works
- [ ] `demos/consent_demo.py` runs; consent flow completes

### 8.3 Pilot Kit

- [ ] `cp .env.example .env && ./scripts/start.sh` starts all services
- [ ] `python examples/create_token.py` creates a token
- [ ] `python examples/apply_policies.py` applies policies
- [ ] `docs/pilot.md` and `docs/pilot-integration.md` exist and are accurate

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/docs` | Developer docs: architecture, getting-started, api-reference |
| `feature/demo-scripts` | Standalone demos: gmail, stripe, revoke, consent |
| `feature/pilot` | Pilot kit: docker-compose, start.sh, examples, pilot docs |

---

## Consistency with Phase 1–7

Phase 8 follows the same structure:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification
- **Branch summary** – Quick reference

Phase 8 is about **adoption and evaluation**: docs so developers understand Alloist quickly, demo scripts to see enforcement in action, and a pilot kit to get started in minutes.
