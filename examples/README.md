# Alloist Examples

## Prerequisites

- Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
- Python 3.11+ with httpx: `pip install httpx`

## Example Agents

Minimal AI agents that call `enforce()` before performing actions. If Alloist policy denies the request, `AlloistPolicyDeniedError` is raised and the action never executes.

| Agent | Description |
|-------|-------------|
| [booking_agent](booking_agent/README.md) | Creates bookings; enforces `booking.create` with price metadata |
| [email_agent](email_agent/README.md) | Sends emails; enforces `gmail.send` with recipient metadata |
| [github_agent](github_agent/README.md) | Pushes code; enforces `github.push` with branch metadata |

Install the SDK: `pip install -e packages/sdk-python`. Run with `ALLOIST_TOKEN=your_token python examples/<agent>/agent.py [args]`.

## Scripts

| Script | Description |
|--------|-------------|
| `create_token.py` | Create a capability token. Usage: `python create_token.py [--subject agent] [--scopes email:send payments] [--ttl 3600]` |
| `apply_policies.py` | Apply policies from `policies.json` to the policy service |
| `policies.json` | Sample policies (deny gmail.send, deny stripe.charge > 1000) |

## Environment

Set or export: `TOKEN_SERVICE_URL`, `TOKEN_SERVICE_API_KEY`, `POLICY_SERVICE_URL`, `POLICY_SERVICE_API_KEY` (defaults work with pilot `.env`).
