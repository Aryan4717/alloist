# ACT-lite Specification

**Agent Capability Token (ACT-lite)** — A concise specification for capability tokens, evidence bundles, and revocation used to gate AI agent actions.

---

## 1. Token (ACT-lite JWT)

### 1.1 Claims

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| `sub` | string | Yes | Subject (agent or user identifier) |
| `scopes` | string[] | Yes | Capability scopes (e.g. `["email:send", "read"]`) |
| `jti` | string | Yes | Unique token ID (UUID). Used for revocation lookup. |
| `iat` | number | Yes | Issued at (Unix seconds) |
| `exp` | number | Yes | Expiration (Unix seconds) |

Optional: `iss` (issuer), `aud` (audience) if needed for multi-tenant deployments.

### 1.2 Header

| Header | Value |
|--------|-------|
| `alg` | `EdDSA` |
| `typ` | `JWT` |
| `kid` | Signing key ID (opaque string, e.g. `key_20260109_a1b2c3d4`) |

### 1.3 Algorithm

- **Signing**: Ed25519 (EdDSA)
- **JWK format**: `kty: OKP`, `crv: Ed25519`, `x` (base64url-encoded raw 32-byte public key), `kid`

### 1.4 Signature Verification (Token)

1. Fetch JWKS from issuer (e.g. `GET /keys`).
2. Read `kid` from JWT header; locate matching key in JWKS.
3. Decode JWT with EdDSA and that public key.
4. Reject if signature invalid, `kid` missing, or key not found.
5. Verify `exp` (Unix seconds); reject if expired. Optional: verify `iat`.
6. Optionally check revocation status (by `jti` or revocation feed).

---

## 2. Evidence Object

### 2.1 Format

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence_id` | string (UUID) | Yes | Unique evidence record ID |
| `action_name` | string | Yes | Action identifier (e.g. `gmail.send`, `stripe.charge`) |
| `token_snapshot` | object | Yes | Snapshot of token claims at evaluation time |
| `timestamp` | string | Yes | ISO 8601 (e.g. `2026-01-09T12:00:00`) |
| `input_hash` | string | Yes | SHA256 hex of canonical JSON of `action_name` + `token_snapshot` + `metadata` |
| `policy_id` | string (UUID) \| null | No | Policy that matched (if any) |
| `result` | string | Yes | `"allow"` or `"deny"` |
| `runtime_metadata` | object | No | Additional context (action metadata, etc.) |
| `public_key` | string | Yes | Base64 Ed25519 public key used for signing |
| `runtime_signature` | string | Yes | Base64 Ed25519 signature (see below) |

### 2.2 Signing

- **Payload to sign**: Canonical JSON (sorted keys, no whitespace) of the bundle **excluding** `runtime_signature`.
- **Signature**: Ed25519 sign over payload bytes; store as base64 in `runtime_signature`.

### 2.3 Verification (Evidence)

1. Parse bundle; extract `runtime_signature` and `public_key`.
2. Build canonical JSON of bundle without `runtime_signature`.
3. Verify Ed25519 signature with `public_key`.
4. Optionally verify `input_hash`: recompute SHA256 of canonical JSON of `{"action_name": ..., "token_snapshot": ..., "metadata": ...}`; must match `input_hash`.

---

## 3. Revocation Semantics

### 3.1 Event Payload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token_id` | string | Yes | Token `jti` being revoked |
| `event` | string | Yes | `"revoked"` |
| `ts` | string | Yes | ISO 8601 timestamp |
| `nonce` | string (UUID) | Yes | Unique per event (replay/dedup) |
| `kid` | string | Yes | Key identifier (e.g. `revocation`) |
| `signature` | string | Yes | Base64 Ed25519 signature |

**Payload to sign**: Canonical JSON (sorted keys) of `token_id`, `event`, `ts`, `nonce` (exclude `kid` and `signature`).

### 3.2 Verification (Revocation)

1. Parse payload; ensure `ts` is present.
2. Reject if `ts` is older than max age (e.g. 120 seconds).
3. Verify Ed25519 signature using revocation public key (from JWKS with `use: "revocation"` or separate endpoint).

### 3.3 Semantics

- A token with `jti` matching a verified revocation event is **invalid** regardless of JWT expiry.
- Enforcers must treat revoked tokens as invalid.
- Optional: push channel (WebSocket, Redis pub/sub) for low-latency revocation propagation.

---

## 4. Key Rotation

### 4.1 Token Signing Keys

- Issuer maintains multiple keys; one **active** for minting new tokens.
- **Rotation**: Create new key, mark active; deactivate previous. Old keys remain in JWKS for verifying existing tokens until they expire.
- **Key ID format**: Opaque string (e.g. `key_YYYYMMDD_hex`).

### 4.2 Revocation / Evidence Signing Keys

- Separate from token signing keys.
- Rotation via configuration or environment variables.
- No JWKS required if keys are fixed per environment; revocation key may be exposed in JWKS with `use: "revocation"` for SDK verification.

---

## 5. Signature Verification Summary

| Artifact | Steps |
|----------|-------|
| **Token** | JWKS → key by `kid` → EdDSA verify → check `exp` → optional revocation check |
| **Evidence** | Extract `runtime_signature`, `public_key` → canonical JSON (no sig) → Ed25519 verify → optional `input_hash` check |
| **Revocation** | Check `ts` max age → Ed25519 verify with revocation key |

---

## 6. References

- JSON Schemas: `schemas/`
- Conformance tests: [CONFORMANCE.md](CONFORMANCE.md)
- Security recommendations: [SECURITY.md](SECURITY.md)
- Examples: `examples/`
