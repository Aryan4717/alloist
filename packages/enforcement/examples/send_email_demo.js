'use strict';

/**
 * Example: Intercept send_email action with enforcement check.
 * Run with: node examples/send_email_demo.js
 *
 * Prerequisites:
 * - Token service running (docker-compose up)
 * - Valid token with scope "email:send" (from POST /tokens)
 */

const { createEnforcement } = require('../src/index.js');

async function sendEmail(token, to, subject, body) {
  const enforcement = createEnforcement({
    apiUrl: process.env.TOKEN_SERVICE_URL || 'http://localhost:8000',
    apiKey: process.env.TOKEN_SERVICE_API_KEY || '',
    failClosed: true,
    highRiskActions: ['send_email'],
  });

  const result = await enforcement.check({
    token,
    action: { name: 'send_email', service: 'email', metadata: { to } },
  });

  if (!result.allowed) {
    throw new Error(`Blocked: ${result.reason} (evidence_id: ${result.evidence_id})`);
  }

  console.log('Sending email...', {
    to,
    subject,
    evidence_id: result.evidence_id,
  });

  enforcement.close();
  // In real app: await actualSendEmail(to, subject, body);
}

// Demo: pass token as first arg
const token = process.argv[2];
if (!token) {
  console.error('Usage: node send_email_demo.js <token>');
  process.exit(1);
}

sendEmail(token, 'user@example.com', 'Test', 'Body').catch((err) => {
  console.error(err.message);
  process.exit(1);
});
