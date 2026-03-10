# Alloist Phase 6

## In Plain English (One-Read Summary)

Phase 6 adds **consent interfaces** so users can approve or deny AI agent actions in real time:

**6.1 Browser Extension** – A Chrome extension that stays connected to Alloist. When an agent tries to do something that requires consent (e.g. charge a card), the request pops up in the extension. You click Approve or Deny. The agent waits for your decision before proceeding.

**6.2 Mobile App** – A React Native app for your phone. Same idea: pending consent requests appear in a list. You can approve or deny from anywhere. Push notifications alert you when new requests arrive so you don't have to keep the app open.

---

## What Phase 6 Includes

| Item | Branch | Description |
|------|--------|-------------|
| **6.1** | `feature/browser-extension` | Chrome extension: WebSocket, popup UI, Approve/Deny |
| **6.2** | `feature/mobile-consent` | React Native + Expo app: pending list, push notifications, device registration |

---

## 6.1 Browser Extension

A Chrome extension that receives consent requests in real time and lets you approve or deny them.

### In plain English

- **WebSocket** – The extension connects to the policy service. When a policy says `require_consent`, the backend broadcasts the request to all connected extensions.
- **Popup** – Click the extension icon to see the pending request: agent name, action (e.g. `stripe.charge`), metadata, risk level. Approve (green) or Deny (red).
- **No polling** – Requests arrive instantly via WebSocket. You don't need to refresh.

### Prerequisites

- Policy service running (port 8001)
- Token created
- Policy with `effect: "require_consent"` for the action

### Build and load

```bash
cd apps/browser-extension
npm install
npm run build
```

In Chrome: `chrome://extensions/` → Developer mode → Load unpacked → select `apps/browser-extension/dist`.

### Configuration

The extension uses `dev-api-key` and `http://localhost:8001` by default. You can change these in the extension options (if implemented) or via `chrome.storage.local` (backendUrl, apiKey, orgId).

### Testing

See [apps/browser-extension/TESTING_GUIDE.md](apps/browser-extension/TESTING_GUIDE.md) for step-by-step instructions.

---

## 6.2 Mobile App

A React Native + Expo app for approving consent requests on your phone.

### In plain English

- **Pending list** – Fetches `GET /consent/pending` to show all pending requests. Pull to refresh.
- **Approve/Deny** – Each request card has Approve and Deny buttons. Submits to `POST /consent/decision`.
- **Push notifications** – When a new consent request is created, the backend sends a push via Expo. Tap the notification to open the app.
- **Device registration** – The app registers your Expo push token with `POST /consent/register-device` so the backend knows where to send notifications.

### Prerequisites

- Policy service running (port 8001)
- Physical device or emulator (use your Mac's IP instead of localhost for physical devices, e.g. `http://192.168.0.131:8001`)

### Run the app

```bash
cd apps/mobile-consent
npm install
npm start
```

### Configuration (Settings screen)

| Setting | Default | Description |
|---------|---------|-------------|
| API Key | `dev-api-key` | API key for policy service |
| Org ID | `00000000-0000-0000-0000-000000000001` | Organization ID |
| Backend URL | `http://localhost:8001` | Policy service URL (use Mac IP for physical device) |

### Backend endpoints (Phase 6)

| Endpoint | Description |
|----------|-------------|
| `GET /consent/pending` | List pending consent requests for the org |
| `POST /consent/decision` | Submit approve or deny |
| `POST /consent/register-device` | Register device for push (Expo push token) |
| `WebSocket /consent/ws` | Real-time consent requests (browser extension) |

---

## Full Testing Checklist (Phase 6)

### 6.1 Browser Extension

- [ ] Start policy service: `cd backend/token_service && docker-compose up -d`
- [ ] Create token and `require_consent` policy (see TESTING_GUIDE.md)
- [ ] Build extension: `cd apps/browser-extension && npm run build`
- [ ] Load unpacked extension from `dist/` in Chrome
- [ ] Trigger `POST /policy/evaluate` with matching action
- [ ] Click extension icon; see request; Approve or Deny
- [ ] Re-evaluate; result should be allow or deny based on decision

### 6.2 Mobile App

- [ ] Run migration: `cd backend/policy_service && alembic upgrade head`
- [ ] Start app: `cd apps/mobile-consent && npm start`
- [ ] Configure Settings (API key, org ID, backend URL)
- [ ] Grant notification permissions
- [ ] Trigger consent request via `POST /policy/evaluate`
- [ ] See request in app; Approve or Deny
- [ ] (Optional) Verify push notification on new request

---

## Branch Summary

| Branch | Purpose |
|--------|---------|
| `feature/browser-extension` | Chrome extension: WebSocket, popup, Approve/Deny |
| `feature/mobile-consent` | React Native app: pending list, push, device registration |

---

## Consistency with Phase 1–5

Phase 6 follows the same structure:

- **Plain English summary** – One-read overview
- **What it includes** – Table of items and branches
- **Per-feature sections** – In plain English, usage, tests
- **Full testing checklist** – Checkboxes for verification

Phase 6 is about **user-facing consent**: the browser extension for desktop users and the mobile app for on-the-go approval, both backed by the same consent APIs.
