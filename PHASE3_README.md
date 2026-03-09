# Alloist Phase 3

## In Plain English (One-Read Summary)

Phase 3 adds two things:

**3.1 Admin website** – A browser-based dashboard where you can see and manage tokens, policies, and evidence without using the command line or APIs directly. You get a Tokens list (create/revoke), Policies list (create/edit/delete), a live stream of enforcement events, and the ability to download evidence bundles. There’s also a short “quickstart” guide that walks you through protecting a demo agent in a few minutes.

**3.2 Policy DSL** – A small, readable way to write policy rules in text (JSON) instead of raw JSON. You describe *what* you want (e.g. “block Stripe charges over 1000”) in simple conditions; the system compiles that into the rules the engine uses. The admin UI has a DSL editor with a “Validate” button so you can check and then save policies.

---

## What Phase 3 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **3.1** | `feature/admin-ui` | Next.js admin console: tokens, policies, live actions, evidence exports, quickstart overlay |
| **3.2** | `feature/policy-dsl` | Declarative policy DSL, compiler, DSL editor and validation in the admin UI |

---

## 3.1 Admin Next.js UI

A web app (Next.js) that talks to the token and policy backends so you can manage everything from the browser.

### In plain English

- **Tokens** – List all tokens, create new ones, revoke them. No need to call the API or use curl.
- **Policies** – List policies, create new ones, edit or delete. You can use prebuilt templates (e.g. block Stripe high value, block Gmail send).
- **Live Actions** – A table that auto-updates with recent “who did what and was it allowed or denied.” It’s the stream of enforcement events (evidence).
- **Evidence Exports** – List evidence and download signed bundles (e.g. for auditors).
- **Quickstart overlay** – On first visit, a short step-by-step overlay shows how to protect a demo agent in a few minutes.

### Prerequisites

- Token service running (port 8000)
- Policy service running (port 8001)
- Signing key created (see Phase 1 / Phase 2)

### Start the admin UI

```bash
cd apps/admin
npm install
npm run dev
```

Open **http://localhost:3000**. When prompted, enter your API key (e.g. `dev-api-key`).

### If you reset the database

If you run a command that drops DB data (e.g. `docker compose down -v`), you need to re-initialize the stack before using the admin UI or demos.

1. **Restart services and recreate DB**

   ```bash
   cd backend/token_service
   docker compose up -d
   ```

   This starts PostgreSQL, **token_service** (port 8000) and **policy_service** (port 8001) and runs Alembic migrations automatically. Wait ~10–15 seconds.

2. **Recreate the signing key (required)**

   ```bash
   cd backend/token_service
   docker compose exec token_service python -m app.cli.rotate_key
   ```

3. **Recreate data via UI / demos**

   - Open the Admin UI:

     ```bash
     cd apps/admin
     npm run dev
     ```

     Go to `http://localhost:3000`, set your API key (e.g. `dev-api-key`), then:
     - Create a token on the **Tokens** page.
     - Create policies on the **Policies** page (or from templates).

   - Or use the demos to repopulate evidence:

     ```bash
     # One-time venv (if not already set up)
     cd /path/to/alloist
     python3 -m venv .venv
     source .venv/bin/activate
     pip install -e packages/enforcement_py httpx

     # Gmail block demo
     cd backend/demos/gmail_block_demo
     python run_demo.py
     ```

   After this, **Live Actions** and **Evidence Exports** in the admin UI will start showing new events and evidence again.

### How to test using the UI

1. **API key** – On first load, enter the API key in the yellow banner (e.g. `dev-api-key`) and click Save.
2. **Tokens**
   - Go to **Tokens**. Click **Create token**, fill subject (e.g. `test-agent`), optional scopes, TTL, then Create.
   - Confirm the new token appears in the table. Click **Revoke** on a token and confirm it shows as revoked.
3. **Policies**
   - Go to **Policies**. Use **Create from template** on a card (e.g. “Block Stripe charges > $1000”) to create a policy.
   - Confirm it appears in “Existing policies.” Click **Edit**, change name or rules, Update. Click **Delete** and confirm removal.
4. **Live Actions**
   - Go to **Live Actions**. Run a demo agent that gets blocked (e.g. Gmail or Stripe demo). Confirm new rows appear (action, result deny, timestamp). Use filters (Result, Action name) and Refresh.
5. **Evidence Exports**
   - Go to **Evidence Exports**. After at least one blocked action, you should see evidence rows. Click **Export** on a row and confirm a JSON file downloads.
6. **Quickstart**
   - If you haven’t dismissed it, follow the overlay steps (start services, create token, add policy, run agent, see block). Dismiss and optionally use “Go to Tokens” / “Live Actions” links.

---

## 3.2 Policy DSL

A small declarative language to define policy rules in text (JSON). The backend compiles it into the same rules the existing policy engine uses.

### In plain English

Instead of writing low-level JSON with `match`, `conditions`, and operators, you write short conditions like:

- `action.service == "stripe"` and `action.name == "charge"`
- `metadata.amount > 1000`
- `"email:send" in token.scopes`

The **DSL compiler** turns these into the internal rule format. The **admin UI** lets you type or paste DSL (JSON), click **Validate DSL**, and then save the policy (and optionally store the DSL for re-editing later).

### Example DSL (JSON)

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

### Supported expressions

- **Action match:** `action.service == "stripe"`, `action.name == "charge"`
- **Numeric:** `metadata.amount > 1000`, `<`, `>=`, `<=`, `==`, `!=`
- **String:** `metadata.currency == "usd"`
- **Scopes:** `"email:send" in token.scopes`

Conditions in the list are AND-ed. The compiler fills `match` from `action.service` / `action.name` and turns the rest into `conditions` for the evaluator.

### How to test using the UI

1. Go to **Policies** in the admin UI.
2. Click **Create policy**. Enter name and description.
3. Switch to the **DSL** tab (next to JSON).
4. Paste or type a DSL JSON array (e.g. the example above). Click **Validate DSL**.
   - If valid: you see a “Valid” indicator; Save is enabled.
   - If invalid: you see error messages; fix the DSL and validate again.
5. Click **Create** (or **Update** when editing). Confirm the policy appears in the list and behaves as expected (e.g. run a demo that should be blocked).
6. **Templates:** Use **Open in DSL** on a template card to open the create form in DSL mode with that template’s snippet; validate and save.
7. **Edit:** Open an existing policy created from DSL; it should re-open in DSL mode with the stored DSL so you can edit and validate again.

### Backend tests (DSL compiler)

```bash
cd backend/policy_service
pip install -r requirements.txt
python -m pytest tests/test_policy_dsl_compile.py tests/test_policy_dsl_integration.py -v
```

---

## Full Testing Checklist (Phase 3)

### 3.1 Admin UI

- [ ] Backend: token service and policy service running (e.g. `cd backend/token_service && docker compose up -d` + signing key).
- [ ] `cd apps/admin && npm install && npm run dev`; open http://localhost:3000.
- [ ] Set API key in the banner.
- [ ] **Tokens:** Create a token, confirm it appears; revoke one, confirm status.
- [ ] **Policies:** Create from template, edit, delete; confirm list updates.
- [ ] **Live Actions:** Trigger a blocked action (e.g. demo); confirm events appear; use filters/refresh.
- [ ] **Evidence Exports:** Export at least one evidence bundle; confirm download.
- [ ] **Quickstart:** See overlay (or clear `alloist_quickstart_dismissed` in localStorage); run through steps and dismiss.

### 3.2 Policy DSL

- [ ] In admin **Policies**, create a policy using the **DSL** tab (e.g. stripe_high_value example).
- [ ] Validate DSL, then save; confirm policy appears and blocks as expected.
- [ ] Use “Open in DSL” on a template; validate and save.
- [ ] Edit a DSL-backed policy; confirm DSL rehydrates; change, validate, update.
- [ ] Run backend DSL tests: `pytest tests/test_policy_dsl_compile.py tests/test_policy_dsl_integration.py -v`.

---

## Environment Variables (Phase 3)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_TOKEN_SERVICE_URL` | `http://localhost:8000` | Token service URL for admin UI |
| `NEXT_PUBLIC_POLICY_SERVICE_URL` | `http://localhost:8001` | Policy service URL for admin UI |

Backend CORS allows `http://localhost:3000` and `http://127.0.0.1:3000` for the admin app.

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/admin-ui` | Next.js admin: tokens, policies, live actions, evidence, quickstart |
| `feature/policy-dsl` | Policy DSL compiler, compile_dsl API, DSL editor and validation in admin |
