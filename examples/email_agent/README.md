# Email Agent

## What the agent does

The email agent simulates an AI agent that sends emails. Before sending, it calls `enforce()` with the action `gmail.send` and metadata (e.g. recipient). If Alloist allows the action, the email is sent. If not, the agent never runs the send logic.

## How Alloist blocks dangerous actions

`enforce()` runs before the actual send. It sends a POST request to `/enforce` with the action and metadata. If Alloist policy denies the request (e.g. "Block Gmail send" policy), the backend returns deny and the SDK raises `AlloistPolicyDeniedError`. The agent catches this and never executes the send. The default `policies.json` includes a policy that denies `gmail.send`, so this agent will be blocked when that policy is applied.

## Prerequisites

- Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
- Capability token minted (`python examples/create_token.py`)
- Policies applied (`python examples/apply_policies.py`) — includes "Block Gmail send"
- Alloist SDK: `pip install -e packages/sdk-python`

## Run

```bash
# From repo root
ALLOIST_TOKEN=your_token python examples/email_agent/agent.py user@example.com
```

Or with args: `python examples/email_agent/agent.py <recipient>`
