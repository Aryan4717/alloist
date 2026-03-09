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
- **Policies** – Create, edit, delete policies; use templates (stripe_high_value_block, gmail_external_send_deny, github_merge_block_without_review)
- **Live Actions** – Stream of enforcement events (evidence), auto-refresh every 5s
- **Evidence Exports** – Download signed evidence bundles

## Quickstart

On first visit, a 5-minute quickstart overlay shows how to protect a demo agent.
