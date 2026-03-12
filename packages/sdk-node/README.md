# @alloist/sdk

Node.js SDK for Alloist policy enforcement. Gate AI agent actions with one line of code.

## Install

```bash
npm install @alloist/sdk
```

Or from the monorepo:

```bash
npm install -e packages/sdk-node
```

## Usage

```typescript
import { init, enforce } from "@alloist/sdk";

// Initialize with your capability token (from minting)
init({ apiKey: process.env.ALLOIST_TOKEN });

// Enforce before performing an action
await enforce("stripe.charge", { amount: 100 });
// Returns on allow; throws on deny

// Proceed with your action
processPayment(100);
```

## Example

```typescript
import { init, enforce } from "@alloist/sdk";

init({ apiKey: process.env.ALLOIST_TOKEN });

try {
  await enforce("gmail.send", { to: "user@gmail.com" });
  // Action allowed - proceed
  await sendEmail({ to: "user@gmail.com", body: "Hello" });
} catch (err) {
  // Action blocked by policy
  console.error("Cannot send email:", err.message);
}
```

## Configuration

Default policy service URL: `http://localhost:8001`

Override with:

```typescript
init({
  apiKey: process.env.ALLOIST_TOKEN,
  policyServiceUrl: "https://policy.example.com",
});
```

## Requirements

- Node.js 18+
- Alloist policy service running with `/enforce` endpoint
