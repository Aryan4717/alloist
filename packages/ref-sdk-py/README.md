# alloist-ref-sdk-py

Minimal ACT-lite reference SDK for Python: token, evidence, and revocation verification only.

## API

```python
from alloist_ref_sdk import (
    verify_token,
    verify_evidence_bundle,
    verify_revocation_payload,
    fetch_revocation_public_key,
)

# Token: verify JWT with JWKS
result = verify_token(token, jwks)
# {"valid": True, "jti", "scopes", "subject"} or {"valid": False, "reason": "..."}

# Evidence: verify signed bundle
ok = verify_evidence_bundle(bundle)

# Revocation: verify signed payload
ok = verify_revocation_payload(payload, public_key_b64=key_b64)

# Fetch revocation key from issuer
key_bytes = fetch_revocation_public_key("http://localhost:8000")
```

## Installation

```bash
pip install alloist-ref-sdk-py
```

## Conformance

Implements ACT-lite spec verification steps. See [spec/CONFORMANCE.md](../../spec/CONFORMANCE.md).
