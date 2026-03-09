# ACT-lite Conformance Test List

Implementations may claim conformance by passing the following tests. Reference by number when reporting conformance.

## Token

| # | Test | Description |
|---|------|-------------|
| 1 | Valid token verifies | A token with required claims (`sub`, `scopes`, `jti`, `iat`, `exp`) and valid signature verifies successfully with the correct JWKS. |
| 2 | Expired token rejected | A token with `exp` in the past is rejected. |
| 3 | Tampered signature rejected | A token with modified payload or wrong signature is rejected. |
| 4 | Missing/unknown kid rejected | A token with missing `kid` in header, or `kid` not present in JWKS, is rejected. |
| 5 | JWKS format | JWKS endpoint returns at least one key with `kty: OKP`, `crv: Ed25519`, and `kid`. |

## Evidence

| # | Test | Description |
|---|------|-------------|
| 6 | Signed bundle verifies | A signed evidence bundle verifies with the bundled `public_key`. |
| 7 | Tampered bundle rejected | A bundle with modified content fails signature verification. |
| 8 | input_hash matches | When `input_hash` is present, it matches the recomputed SHA256 of `action_name` + `token_snapshot` + `metadata` (canonical JSON). |
| 9 | Required fields present | Bundle contains all required fields: `evidence_id`, `action_name`, `token_snapshot`, `timestamp`, `input_hash`, `result`, `runtime_signature`, `public_key`. |

## Revocation

| # | Test | Description |
|---|------|-------------|
| 10 | Signed payload verifies | A signed revocation payload verifies with the revocation public key. |
| 11 | Stale payload rejected | A payload with `ts` older than max age (e.g. 120s) is rejected. |
| 12 | Tampered payload rejected | A payload with modified content fails signature verification. |

## Key Rotation

| # | Test | Description |
|---|------|-------------|
| 13 | New token uses new key | After rotation, newly minted tokens use the new active key; tokens minted before rotation still verify with the old key in JWKS until expiry. |
| 14 | Revocation key identifiable | Revocation public key is identifiable (e.g. `use: "revocation"` in JWKS) and revocation payload verification succeeds with it. |
