# ACT-lite Security Recommendations

Minimal security guidance for implementers of the Agent Capability Token (ACT-lite) specification.

## Transport

- **HTTPS**: Use HTTPS for JWKS (`/keys`), revocation, and evidence endpoints. Never serve keys or accept tokens over plain HTTP in production.

## Tokens

- **Short TTL**: Prefer short token lifetimes; combine with revocation for immediate invalidation when needed.
- **Scope minimization**: Issue tokens with the minimum scopes required for the agent's intended actions.

## Key Management

- **Private keys**: Store private keys in a secure vault (e.g. HSM, cloud KMS). Never log, expose, or commit private keys.
- **Key rotation**: Rotate token signing keys periodically; deactivate old keys but keep them in JWKS until all tokens signed with them have expired.

## Revocation

- **Max age**: Enforce a maximum age (e.g. 120 seconds) on revocation payloads to limit replay. Reject older payloads.
- **Nonce**: Use the `nonce` field for deduplication when processing revocation events from multiple sources.

## Evidence

- **input_hash**: Verify `input_hash` when auditing evidence bundles to detect tampering of action or token snapshot.
- **Public key pinning**: For high-assurance verification, pin or distribute the evidence signing public key out-of-band rather than trusting it from the bundle alone.

## General

- **Principle of least privilege**: Grant agents only the capabilities they need.
- **Audit logging**: Log enforcement decisions (allow/deny) and evidence for compliance and forensics.
