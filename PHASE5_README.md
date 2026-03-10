# Alloist Phase 5

## In Plain English (One-Read Summary)

Phase 5 makes Alloist **team-ready and production-oriented**:

**5.1 Organization RBAC** – Different people get different powers. Admins can do everything (create tokens, revoke, delete policies). Developers can create and edit. Viewers can only look. Each org has its own members and roles. You pick who sees what.

**5.2 Audit Retention** – Your audit logs don't pile up forever. Each org sets how long to keep them (e.g. 30 days). Old logs are automatically deleted on a schedule. You can still list and export logs (JSON or CSV) for the time range you care about.

**5.3 SSO (Single Sign-On)** – Log in with Google or GitHub instead of typing an API key. The admin UI redirects you to sign in, then brings you back with a session. SAML is stubbed for future enterprise SSO.

**5.4 Billing Stub** – A foundation for paid plans. Orgs have subscriptions (free, startup, enterprise) and usage is tracked (tokens created, policy evaluations, enforcement checks). When you hit the limit, requests are blocked. Stripe checkout is a placeholder for now.

---

## What Phase 5 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **5.1** | `feature/org-rbac` | Org-scoped roles (admin/developer/viewer), require_role, API keys per user |
| **5.2** | `feature/audit-retention` | Audit logs, retention_days per org, auto-cleanup, list/export |
| **5.3** | `feature/sso` | OAuth (Google, GitHub), JWT sessions, admin login/callback |
| **5.4** | `feature/billing-stub` | Subscriptions, org_usage, plan limits, usage blocking, Stripe placeholder |

---

## 5.1 Organization RBAC

Users belong to organizations. Each membership has a role: **admin**, **developer**, or **viewer**.

### In plain English

- **Admin** – Full control: create/revoke tokens, create/edit/delete policies, manage billing, see everything.
- **Developer** – Can create tokens and policies, run evaluations, view audit logs. Cannot revoke tokens or delete policies.
- **Viewer** – Read-only: list tokens, policies, audit logs, evidence. Cannot create or change anything.

Every API call is scoped to an org via the `X-Org-Id` header. The backend checks that the user (from JWT or API key) is in that org and has the right role for the action.

### Roles by Route

| Route | Admin | Developer | Viewer |
|-------|-------|-----------|--------|
| List tokens | ✓ | ✓ | ✓ |
| Mint token | ✓ | ✓ | ✗ |
| Revoke token | ✓ | ✗ | ✗ |
| List policies | ✓ | ✓ | ✓ |
| Create/update policy | ✓ | ✓ | ✗ |
| Delete policy | ✓ | ✗ | ✗ |
| Evaluate policy | ✓ | ✓ | ✓ |
| Audit logs / export | ✓ | ✓ | ✓ |
| Billing checkout | ✓ | ✗ | ✗ |
| Billing subscription | ✓ | ✓ | ✓ |

### How It Works

- **JWT** – After OAuth login, the session token includes `org_id` and `role`. The backend uses these for authorization.
- **API keys** – Each key is tied to a user. The user's org memberships and roles determine what the key can do.
- **X-Org-Id** – When you have multiple orgs, you pass the org you're acting in. The backend verifies you're a member.

---

## 5.2 Audit Retention

Audit logs record every policy evaluation (allow/deny). Retention controls how long they're kept.

### In plain English

- **Audit logs** – Each row has: org, action (e.g. `stripe.charge`), result (allow/deny), metadata, timestamp.
- **Retention** – Each org has `retention_days` (default 30). Logs older than that are deleted.
- **Cleanup** – A background task runs every hour (configurable) and deletes expired logs per org.
- **Export** – You can list logs with filters (since, until, result) and export as JSON or CSV.

### API

| Endpoint | Description |
|----------|-------------|
| `GET /audit/logs` | List logs with `since`, `until`, `result`, `limit`, `offset` |
| `GET /audit/export?format=json\|csv` | Export logs as JSON or CSV |

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_CLEANUP_INTERVAL_SEC` | `3600` | Seconds between retention cleanup runs |

`retention_days` is stored per organization in the database (default 30).

---

## 5.3 SSO (Single Sign-On)

Log in with Google or GitHub. No API key needed for the admin UI.

### In plain English

- **Login page** – Admin UI shows "Login with Google" and "Login with GitHub".
- **OAuth flow** – Click → redirect to provider → sign in → redirect back with a JWT.
- **Session** – JWT is stored in the browser. It includes user id, email, org, and role.
- **Org switcher** – If you're in multiple orgs, you can switch which one you're acting in.
- **SAML** – Placeholder only (`/auth/saml/login` returns 501). For future enterprise SSO.

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /auth/google/login` | Redirect to Google OAuth |
| `GET /auth/google/callback` | Exchange code, create/fetch user, issue JWT, redirect to frontend |
| `GET /auth/github/login` | Redirect to GitHub OAuth |
| `GET /auth/github/callback` | Same as Google |
| `GET /auth/me` | Return current user and orgs (JWT or API key) |
| `GET /auth/saml/login` | 501 – SAML not implemented |

### Configuration

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | Callback URL (e.g. `http://localhost:8000/auth/google/callback`) |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |
| `GITHUB_REDIRECT_URI` | Callback URL |
| `AUTH_CALLBACK_URL` | Where to redirect after OAuth (e.g. `http://localhost:3000/auth/callback`) |
| `JWT_SECRET` | Secret for signing session JWTs |
| `JWT_EXPIRY_SECONDS` | Session lifetime (default 3600) |

### Admin UI Flow

1. Open `http://localhost:3000` → redirect to `/login`.
2. Click "Login with Google" or "Login with GitHub".
3. Sign in at the provider.
4. Redirect to `/auth/callback?token=...` → token stored in localStorage → redirect to `/`.
5. Admin UI uses `Authorization: Bearer <token>` for all API calls.

---

## 5.4 Billing Stub

A foundation for usage-based plans. Tracks usage and blocks when limits are exceeded.

### In plain English

- **Plans** – Free, Startup, Enterprise. Each has limits on tokens created, policy evaluations, and enforcement checks.
- **Usage** – Counted per org per month. Resets at the start of each billing period.
- **Blocking** – When you hit the limit (e.g. 10 tokens on free), the API returns 403 with "Usage limit exceeded. Upgrade your plan."
- **Stripe** – Checkout is a placeholder (501). Real Stripe integration comes later.

### Plan Limits

| Plan | enforcement_checks | tokens_created | policy_evaluations |
|------|--------------------|----------------|--------------------|
| free | 100 | 10 | 100 |
| startup | 10,000 | 500 | 10,000 |
| enterprise | unlimited | unlimited | unlimited |

### Usage Metrics

- **tokens_created** – Incremented when `POST /tokens` mints a token.
- **policy_evaluations** – Incremented when `POST /policy/evaluate` is called without `X-Request-Type: enforcement`.
- **enforcement_checks** – Incremented when `POST /policy/evaluate` is called with `X-Request-Type: enforcement` (SDK enforcement flow).

### API

| Endpoint | Description |
|----------|-------------|
| `POST /billing/checkout` | 501 – Stripe checkout placeholder |
| `GET /billing/subscription` | Current org subscription, usage, and limits |

### Database

- **subscriptions** – One per org: plan, status (active/canceled/past_due).
- **org_usage** – Per org per month: enforcement_checks, tokens_created, policy_evaluations.

---

## Full Testing Checklist (Phase 5)

### 5.1 Org RBAC

- [ ] Create users with different roles (admin, developer, viewer) in an org.
- [ ] As viewer: list tokens ✓, mint token ✗ (403).
- [ ] As developer: mint token ✓, revoke token ✗ (403).
- [ ] As admin: revoke token ✓, delete policy ✓.
- [ ] Call with `X-Org-Id` for an org you're not in → 403.

### 5.2 Audit Retention

- [ ] Run policy evaluations; confirm logs appear in `GET /audit/logs`.
- [ ] Export as JSON: `GET /audit/export?format=json`.
- [ ] Export as CSV: `GET /audit/export?format=csv`.
- [ ] Set `retention_days` on an org; run cleanup; confirm old logs deleted.
- [ ] Run policy service tests: `cd backend/policy_service && pytest tests/test_audit.py -v`

### 5.3 SSO

- [ ] Configure Google OAuth (client ID, secret, redirect URI).
- [ ] Open admin UI → Login → "Login with Google" → sign in → land on dashboard.
- [ ] Configure GitHub OAuth; repeat with "Login with GitHub".
- [ ] `GET /auth/me` with JWT returns user and orgs.
- [ ] Run auth tests: `cd backend/token_service && pytest tests/test_auth.py -v`

### 5.4 Billing

- [ ] `GET /billing/subscription` returns subscription, usage, limits.
- [ ] Mint tokens until free limit (10); next mint returns 403.
- [ ] Run policy evaluations until limit; next evaluate returns 403.
- [ ] `POST /billing/checkout` returns 501 with placeholder message.
- [ ] Run migration: `cd backend/token_service && alembic upgrade head`

---

## Environment Variables (Phase 5)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUDIT_CLEANUP_INTERVAL_SEC` | `3600` | Audit retention cleanup interval (policy service) |
| `GOOGLE_CLIENT_ID` | - | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | - | Google OAuth |
| `GITHUB_CLIENT_ID` | - | GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | - | GitHub OAuth |
| `AUTH_CALLBACK_URL` | `http://localhost:3000/auth/callback` | Post-OAuth redirect |
| `JWT_SECRET` | `change-me-in-production` | Session JWT signing |
| `JWT_EXPIRY_SECONDS` | `3600` | Session lifetime |

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/org-rbac` | Org roles, require_role, API keys per user |
| `feature/audit-retention` | Audit logs, retention_days, auto-cleanup, list/export |
| `feature/sso` | OAuth (Google, GitHub), JWT sessions, admin login |
| `feature/billing-stub` | Subscriptions, usage tracking, plan limits, Stripe placeholder |

---

## Consistency with Phase 1–4

Phase 5 follows the same structure:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification
- **Environment** – Config variables

Phase 5 is about **teams and production**: RBAC for who can do what, audit retention for compliance, SSO for easy login, and a billing foundation for paid plans.
