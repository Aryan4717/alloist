# GitHub Agent

## What the agent does

The GitHub agent simulates an AI agent that pushes code to a repository. Before pushing, it calls `enforce()` with the action `github.push` and metadata (e.g. branch). If Alloist allows the action, the push proceeds. If not, the agent never runs the push logic.

## How Alloist blocks dangerous actions

`enforce()` runs before the actual push. It sends a POST request to `/enforce` with the action and metadata. If Alloist policy denies the request (e.g. "deny pushes to main" or "require consent for github.push"), the backend returns deny and the SDK raises `AlloistPolicyDeniedError`. The agent catches this and never executes the push. You can add policies like "deny github.push when branch is main" to prevent risky direct pushes.

## Prerequisites

- Alloist services running (`./scripts/start.sh` or `docker compose up -d`)
- Capability token minted (`python examples/create_token.py`)
- Policies applied (`python examples/apply_policies.py`) — add a policy for `github.push` if needed
- Alloist SDK: `pip install -e packages/sdk-python`

## Run

```bash
# From repo root
ALLOIST_TOKEN=your_token python examples/github_agent/agent.py main
```

Or with args: `python examples/github_agent/agent.py <branch>`
