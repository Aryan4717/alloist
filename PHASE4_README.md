# Alloist Phase 4

## In Plain English (One-Read Summary)

Phase 4 makes Alloist **open-source and interoperable**:

**4.1 ACT-lite spec** – A publishable specification (alloist/spec) for capability tokens, evidence bundles, and revocation. Anyone can implement it. Includes JSON schemas, conformance tests, security recommendations, and examples.

**4.2 Reference SDKs + Conformance Tests** – Minimal verification-only implementations (ref-sdk-node, ref-sdk-py) and an automated test harness. Third-party frameworks (LangChain, Cursor) get integration docs so they can gate agent actions with Alloist.

---

## What Phase 4 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **4.1** | `feature/spec-act-lite` | ACT-lite spec: token, evidence, revocation; JSON schemas; conformance list |
| **4.2** | `feature/ref-sdk-tests` | Reference SDKs (Node, Python), conformance harness, integration docs |

---

## 4.1 ACT-lite Specification

The **Agent Capability Token (ACT-lite)** spec defines how tokens, evidence, and revocation work so other implementations can interoperate.

### In plain English

- **Token** – JWT with subject, scopes, jti, iat, exp. Signed with Ed25519. Enforcers verify before allowing actions.
- **Evidence** – Signed record of each allow/deny decision for auditing. Includes action_name, token_snapshot, input_hash, result.
- **Revocation** – Signed event that invalidates a token immediately. Max age 120s; verified with revocation public key.

### Documents

| Document | Description |
|----------|-------------|
| [spec/SPEC.md](spec/SPEC.md) | Full spec: token claims, evidence format, revocation semantics, key rotation |
| [spec/CONFORMANCE.md](spec/CONFORMANCE.md) | Numbered conformance tests (1–14) for implementations |
| [spec/SECURITY.md](spec/SECURITY.md) | Security recommendations |
| [spec/README.md](spec/README.md) | Overview and links |

### JSON Schemas

| Schema | Description |
|--------|-------------|
| `spec/schemas/act_lite_token_claims.json` | JWT claims |
| `spec/schemas/act_lite_jwks.json` | JWKS response |
| `spec/schemas/evidence_bundle.json` | Evidence bundle |
| `spec/schemas/revocation_payload.json` | Revocation event |

### Conformance Tests (spec)

| # | Area | Test |
|---|------|------|
| 1–5 | Token | Valid verifies, expired rejected, tampered rejected, unknown kid rejected, JWKS format |
| 6–9 | Evidence | Signed verifies, tampered rejected, input_hash matches, required fields present |
| 10–12 | Revocation | Signed verifies, stale rejected, tampered rejected |
| 13–14 | Key rotation | New token uses new key, revocation key identifiable |

---

## 4.2 Reference SDKs + Conformance Tests

Minimal verification-only implementations and an automated harness that runs conformance tests.

### 4.2.1 ref-sdk-node

**Location**: `packages/ref-sdk-node/`

Verification only: no policy, no WebSocket, no full enforcement flow.

**API**:

```javascript
const {
  verifyToken,
  verifyEvidenceBundle,
  verifyRevocationPayload,
  fetchRevocationPublicKey,
} = require('@alloist/ref-sdk-node');

// Token
const result = await verifyToken(token, jwks);
// { valid: true, jti, scopes, subject } | { valid: false, reason }

// Evidence
const ok = verifyEvidenceBundle(bundle);

// Revocation
const ok = verifyRevocationPayload(payload, publicKey);

// Fetch revocation key
const key = await fetchRevocationPublicKey('http://localhost:8000');
```

**Install**:

```bash
npm install @alloist/ref-sdk-node
```

**Tests**:

```bash
cd packages/ref-sdk-node
npm test
```

---

### 4.2.2 ref-sdk-py

**Location**: `packages/ref-sdk-py/`

Same API as Node, Python.

**API**:

```python
from alloist_ref_sdk import (
    verify_token,
    verify_evidence_bundle,
    verify_revocation_payload,
    fetch_revocation_public_key,
)

# Token
result = verify_token(token, jwks)
# {"valid": True, "jti": ..., "scopes": ..., "subject": ...} or {"valid": False, "reason": ...}

# Evidence
ok = verify_evidence_bundle(bundle)

# Revocation
ok = verify_revocation_payload(payload, public_key_b64="...")

# Fetch revocation key
key = fetch_revocation_public_key("http://localhost:8000")
```

**Install**:

```bash
pip install -e packages/ref-sdk-py
```

**Tests**:

```bash
cd packages/ref-sdk-py
pytest tests/ -v
```

---

### 4.2.3 Conformance Harness

**Location**: `packages/conformance/`

Automated runner that executes conformance tests 1–12 plus revoke propagation.

**Structure**:

```
packages/conformance/
├── package.json
├── fixtures/             # Generated test data (tokens, evidence, revocation)
├── scripts/generate_fixtures.js
├── tests/
│   ├── conformance.test.js      # Tests 1–12
│   └── revoke_propagation.test.js   # Mock WebSocket server + client
└── runner.js
```

**Run conformance**:

```bash
make conformance
```

Or:

```bash
cd packages/conformance
npm install
npm run generate   # Generate fixtures (if needed)
npm test
```

**Test mapping** (to [spec/CONFORMANCE.md](spec/CONFORMANCE.md)):

| Conformance # | Test | Fixture |
|---------------|------|---------|
| 1 | Valid token verifies | valid_token.jwt + jwks.json |
| 2 | Expired token rejected | expired_token.jwt |
| 3 | Tampered signature rejected | tampered_token.jwt |
| 4 | Unknown kid rejected | JWKS with wrong kid |
| 5 | JWKS format | jwks.json (OKP, Ed25519, kid) |
| 6 | Signed bundle verifies | valid_evidence_bundle.json |
| 7 | Tampered bundle rejected | tampered_evidence_bundle.json |
| 8 | input_hash matches | valid bundle with input_hash |
| 9 | Required fields present | Schema check |
| 10 | Signed revocation verifies | valid_revocation_payload.json |
| 11 | Stale payload rejected | stale_revocation_payload.json |
| 12 | Tampered payload rejected | tampered_revocation_payload.json |
| P | Revoke propagation | Mock WebSocket: server publishes, client receives & verifies |

---

### 4.2.4 Integration Documentation

**Location**: `docs/integrations/`

| File | Description |
|------|-------------|
| [docs/integrations/langchain.md](docs/integrations/langchain.md) | Wrap LangChain tools with `createEnforcement`; Node and Python examples |
| [docs/integrations/cursor.md](docs/integrations/cursor.md) | Cursor rules, pre-action hooks, Admin UI reference |

---

## Full Testing Checklist (Phase 4)

### 4.1 ACT-lite Spec

- [ ] Review [spec/SPEC.md](spec/SPEC.md), [spec/CONFORMANCE.md](spec/CONFORMANCE.md)
- [ ] Verify JSON schemas in `spec/schemas/` validate example payloads

### 4.2 Reference SDKs

- [ ] `cd packages/ref-sdk-node && npm test`
- [ ] `cd packages/ref-sdk-py && pytest tests/ -v`

### 4.2 Conformance Harness

- [ ] `make conformance` (or `cd packages/conformance && npm run generate && npm test`)
- [ ] Confirm 13/13 passed (12 conformance + 1 revoke propagation)

### 4.2 Integration Docs

- [ ] Review [docs/integrations/langchain.md](docs/integrations/langchain.md)
- [ ] Review [docs/integrations/cursor.md](docs/integrations/cursor.md)

---

## Project Structure (Phase 4 Additions)

```
alloist/
├── spec/                   # ACT-lite spec (4.1)
│   ├── SPEC.md
│   ├── CONFORMANCE.md
│   ├── SECURITY.md
│   ├── schemas/
│   └── examples/
├── packages/
│   ├── ref-sdk-node/       # Minimal Node verification (4.2)
│   ├── ref-sdk-py/         # Minimal Python verification (4.2)
│   └── conformance/        # Test harness (4.2)
├── docs/
│   └── integrations/       # LangChain, Cursor (4.2)
│       ├── langchain.md
│       └── cursor.md
└── Makefile                # make conformance
```

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/spec-act-lite` | ACT-lite spec, schemas, conformance list |
| `feature/ref-sdk-tests` | ref-sdk-node, ref-sdk-py, conformance harness, integration docs |

---

## Consistency with Phase 1–3

Phase 4 follows the same structure as earlier phases:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification
- **Environment / structure** – Where things live
- **Branch summary** – Quick reference

Phase 4 is about **openness and interoperability**: the spec lets others implement ACT-lite; the ref SDKs and conformance harness prove the spec works; integration docs help third-party frameworks (LangChain, Cursor) adopt Alloist.
