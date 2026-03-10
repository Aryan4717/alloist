# Alloist Consent - Mobile App

React Native + Expo app for approving AI agent actions in real time.

## Setup

1. Install dependencies: `npm install`
2. Start the backend: `cd backend/token_service && docker-compose up -d`
3. Run migration: `cd backend/policy_service && alembic upgrade head` (or let Docker run it)
4. Start the app: `npm start`

## Configuration

On first launch, tap **Settings** and configure:

- **API Key**: `dev-api-key` (default)
- **Org ID**: `00000000-0000-0000-0000-000000000001` (default)
- **Backend URL**: `http://localhost:8001` (use `http://10.0.2.2:8001` for Android emulator)

## Push Notifications

- Grant notification permissions when prompted
- The app registers your device with the backend for push when new consent requests arrive
- Push requires a physical device; Expo Go supports push tokens

## Testing

1. Create a token and policy (see browser extension testing guide)
2. Trigger a consent request via `POST /policy/evaluate`
3. The request appears in the app; tap Approve or Deny
