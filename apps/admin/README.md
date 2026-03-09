# Alloist Admin UI

Next.js admin console for managing tokens, policies, and evidence.

## Prerequisites

- Token service running (port 8000)
- Policy service running (port 8001)
- Signing key created for token service

## Setup

```bash
cd apps/admin
npm install
```

## Environment

Create `.env.local` (optional):

```
NEXT_PUBLIC_TOKEN_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_POLICY_SERVICE_URL=http://localhost:8001
```

Defaults: `http://localhost:8000` and `http://localhost:8001`.

## Run

```bash
npm run dev
```

Open http://localhost:3000. Enter your API key (e.g. `dev-api-key`) when prompted.

## Pages

- **Tokens** – Create and revoke capability tokens
- **Policies** – Create, edit, delete policies; use templates or write policies in DSL (declarative YAML/JSON) or raw JSON
- **Live Actions** – Stream of enforcement events (evidence), auto-refresh every 5s
- **Evidence Exports** – Download signed evidence bundles

## Policy DSL

Policies can be written in a small declarative DSL. Example:

```json
[
  {
    "id": "stripe_high_value",
    "description": "Block charges > 1000",
    "conditions": [
      "action.service == \"stripe\"",
      "action.name == \"charge\"",
      "metadata.amount > 1000"
    ],
    "effect": "deny"
  }
]
```

Supported expressions: `action.service == "x"`, `action.name == "y"`, `metadata.field > value`, `"scope" in token.scopes`. Use "Validate DSL" before saving.

## Quickstart

On first visit, a 5-minute quickstart overlay shows how to protect a demo agent.
