# Alloist Examples

## Prerequisites

- Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
- Python 3.11+ with httpx: `pip install httpx`

## Scripts

| Script | Description |
|--------|-------------|
| `create_token.py` | Create a capability token. Usage: `python create_token.py [--subject agent] [--scopes email:send payments] [--ttl 3600]` |
| `apply_policies.py` | Apply policies from `policies.json` to the policy service |
| `policies.json` | Sample policies (deny gmail.send, deny stripe.charge > 1000) |

## Environment

Set or export: `TOKEN_SERVICE_URL`, `TOKEN_SERVICE_API_KEY`, `POLICY_SERVICE_URL`, `POLICY_SERVICE_API_KEY` (defaults work with pilot `.env`).
