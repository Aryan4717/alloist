# YC Demo – Full Flow

Demo script for recording the Phase 1 MVP: token + policy, block, revoke mid-flow, export + verify evidence.

## Flow

1. Create token + policy to block Gmail send
2. Run agent attempt → blocked (show evidence_id)
3. Revoke token mid-flow
4. Run agent again → blocked (token_revoked)
5. Export evidence package → verify signature

## Prerequisites

- Docker (token service, policy service running)
- Python 3.10+ with venv
- `pip install -e packages/enforcement_py httpx` (from repo root)

## Run

```bash
cd backend/demos/yc_demo
python run_demo.py
```

Ensure services are up:

```bash
cd backend/token_service
docker compose up -d
docker compose exec token_service python -m app.cli.rotate_key  # first time only
```
