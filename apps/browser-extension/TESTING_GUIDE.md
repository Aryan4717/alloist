# Alloist Consent Extension – Testing Guide

## Step-by-step (in order)

### Step 1: Start backend and fix WebSocket

```bash
cd backend/token_service
docker-compose up -d --build policy_service
```

Wait ~30 seconds for the service to start.

---

### Step 2: Create a token

```bash
curl -X POST http://localhost:8000/tokens \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{"subject":"test-agent","scopes":["email:send"],"ttl_seconds":3600}'
```

Copy the `token_id` from the response (e.g. `6ee48caf-5f2d-4a3b-b129-2ea0d8cba2a9`).

---

### Step 3: Create the require_consent policy

```bash
curl -X POST http://localhost:8001/policy \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Require consent for stripe.charge",
    "rules": {
      "effect": "require_consent",
      "match": {"service": "stripe", "action_name": "charge"},
      "conditions": []
    }
  }'
```

---

### Step 4: Build and load the extension

```bash
cd apps/browser-extension
npm run build
```

In Chrome:

1. Go to `chrome://extensions/`
2. Turn on **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `dist` folder inside `apps/browser-extension`
5. Click **Select**

---

### Step 5: Pin the extension icon

1. In the Chrome toolbar (top right, near the address bar), click the **puzzle piece** icon.
2. Find **Alloist Consent** in the list.
3. Click the **pin** icon next to it (so it stays in the toolbar).
4. Close the menu (click elsewhere).

You should now see a grey square with an **A** in the toolbar.

---

### Step 6: Trigger a consent request

In your terminal, run (replace with your token_id):

```bash
curl -X POST http://localhost:8001/policy/evaluate \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "token_id": "6ee48caf-5f2d-4a3b-b129-2ea0d8cba2a9",
    "action": {
      "service": "stripe",
      "name": "charge",
      "metadata": {"amount": 50, "currency": "usd"}
    }
  }'
```

You should get: `"reason": "pending_consent"`.

---

### Step 7: Open the popup and Approve/Deny

1. In the Chrome toolbar, click the **Alloist Consent** icon (grey square with **A**).
2. A small popup opens below it.
3. You should see:
   - **Action approval**
   - Agent: test-agent
   - Action: stripe.charge
   - Metadata: {...}
   - Risk: medium
   - **Approve** (green) and **Deny** (red) buttons
4. Click **Approve** or **Deny**.

---

## If you see "No pending requests"

- The WebSocket may still be failing (403). Rebuild: `docker-compose up -d --build policy_service`
- Trigger the curl again, then immediately click the extension icon.
- Reload the extension on `chrome://extensions/` and try again.

---

## Visual reference

| What you click | Where it is |
|----------------|-------------|
| Puzzle piece | Top-right of Chrome, next to your profile icon |
| Pin icon | Next to "Alloist Consent" in the puzzle menu |
| Alloist Consent icon | Grey square with "A" in the toolbar (after pinning) |
| Approve / Deny | Inside the popup that opens when you click the Alloist icon |
