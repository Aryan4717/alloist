# @alloist/ref-sdk-node

Minimal ACT-lite reference SDK for Node.js: token, evidence, and revocation verification only.

## API

```javascript
const {
  verifyToken,
  verifyEvidenceBundle,
  verifyRevocationPayload,
  fetchRevocationPublicKey,
} = require('@alloist/ref-sdk-node');

// Token: verify JWT with JWKS
const result = await verifyToken(token, jwks);
// { valid: true, jti, scopes, subject } | { valid: false, reason }

// Evidence: verify signed bundle
const ok = verifyEvidenceBundle(bundle);

// Revocation: verify signed payload
const ok = verifyRevocationPayload(payload, publicKey);

// Fetch revocation key from issuer
const key = await fetchRevocationPublicKey('http://localhost:8000');
```

## Installation

```bash
npm install @alloist/ref-sdk-node
```

## Conformance

Implements ACT-lite spec verification steps. See [spec/CONFORMANCE.md](../../spec/CONFORMANCE.md).
