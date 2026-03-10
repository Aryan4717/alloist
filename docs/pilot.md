# Pilot Deployment

Get Alloist running in minutes for evaluation and development.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

```bash
# 1. Copy env file
cp .env.example .env

# 2. Start services
./scripts/start.sh
```

Or manually:

```bash
cp .env.example .env
docker compose up -d
# Wait ~15 seconds, then create signing key (first run only):
docker compose exec token_service python -m app.cli.rotate_key
```

## Create Token and Apply Policies

```bash
# Create a capability token
python examples/create_token.py

# Apply example policies (deny gmail.send, deny stripe.charge > 1000)
python examples/apply_policies.py
```

## Verify

- Token Service: http://localhost:8000/docs
- Policy Service: http://localhost:8001/docs
- JWKS: http://localhost:8000/keys

## Integrate with Agents

See [pilot-integration.md](pilot-integration.md) for LangChain, Python, and Node integration instructions.
