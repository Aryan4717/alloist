# ACT-lite (Agent Capability Token)

A concise specification for capability tokens, evidence bundles, and revocation used to gate AI agent actions.

## What is ACT-lite?

- **Token**: A JWT that encodes an agent's capabilities (subject, scopes) and is signed by an issuer. Enforcers verify the token before allowing actions.
- **Evidence**: A signed record of each enforcement decision (allow/deny) for auditing and compliance.
- **Revocation**: A signed event that invalidates a token immediately, regardless of expiry.

## Documents

| Document | Description |
|----------|-------------|
| [SPEC.md](SPEC.md) | Full specification: token fields, evidence format, revocation semantics, key rotation, verification steps |
| [CONFORMANCE.md](CONFORMANCE.md) | Numbered conformance test list for implementations |
| [SECURITY.md](SECURITY.md) | Minimal security recommendations |

## JSON Schemas

| Schema | Description |
|--------|-------------|
| [schemas/act_lite_token_claims.json](schemas/act_lite_token_claims.json) | JWT claims |
| [schemas/act_lite_jwks.json](schemas/act_lite_jwks.json) | JWKS response |
| [schemas/evidence_bundle.json](schemas/evidence_bundle.json) | Evidence bundle |
| [schemas/revocation_payload.json](schemas/revocation_payload.json) | Revocation event |

## Examples

See [examples/](examples/) for sample token claims, evidence bundles, and revocation payloads. All values are illustrative; no real secrets.

## Verifying Evidence

The Alloist reference implementation includes a verification script:

```bash
cd backend/policy_service
python scripts/verify_evidence.py path/to/evidence_bundle.json [--public-key BASE64]
```

Exit 0 if valid, 1 if invalid or tampered.

## License

This spec and schemas are under [LICENSE](LICENSE) (MIT). The ACT-lite spec lives in `spec/` and may be published as **alloist/spec**.
