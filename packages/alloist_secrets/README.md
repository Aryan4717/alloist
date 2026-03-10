# alloist-secrets

Secure secret management for Alloist. Cascade: env vars -> AWS Secrets Manager -> Hashicorp Vault.

## Usage

```python
from alloist_secrets import get, validate_required, register_secret_key

# Get secret (returns None if not found)
api_key = get("TOKEN_SERVICE_API_KEY")

# Validate at startup
validate_required(["DATABASE_URL", "TOKEN_SERVICE_API_KEY"])

# Register keys for log redaction
register_secret_key("TOKEN_SERVICE_API_KEY")
```

## Providers

1. **Env** (default): `os.environ` + optional `.env` file
2. **AWS**: Set `SECRET_PROVIDER_AWS=1` and `AWS_SECRET_NAME`
3. **Vault**: Set `SECRET_PROVIDER_VAULT=1`, `VAULT_ADDR`, `VAULT_TOKEN`

## Install

```bash
pip install -e ../../packages/alloist_secrets
# Optional: pip install alloist-secrets[aws]  # for AWS
# Optional: pip install alloist-secrets[vault]  # for Vault
```
