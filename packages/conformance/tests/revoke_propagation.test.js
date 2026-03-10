'use strict';

/**
 * Revoke propagation conformance test.
 * Mock WebSocket server publishes signed revocation; clients connect, receive, verify,
 * and assert token_id is in revoked set.
 */

const crypto = require('crypto');
const { WebSocketServer } = require('ws');
const { verifyRevocationPayload } = require('@alloist/ref-sdk-node');

function createMockRevocationServer() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const pubRaw = publicKey.export({ format: 'jwk' });
  const pubKeyBytes = Buffer.from(pubRaw.x, 'base64url');

  function signRevocation(tokenId) {
    const payload = {
      token_id: tokenId,
      event: 'revoked',
      ts: new Date().toISOString(),
      nonce: crypto.randomUUID(),
    };
    const canonical = JSON.stringify({
      event: payload.event,
      nonce: payload.nonce,
      token_id: payload.token_id,
      ts: payload.ts,
    });
    const sig = crypto.sign(null, Buffer.from(canonical, 'utf8'), privateKey);
    return { ...payload, kid: 'revocation', signature: sig.toString('base64') };
  }

  const clients = [];
  const wss = new WebSocketServer({ port: 0 });

  wss.on('connection', (ws) => {
    clients.push(ws);
  });

  function broadcastRevocation(tokenId) {
    const payload = signRevocation(tokenId);
    const msg = JSON.stringify(payload);
    for (const ws of clients) {
      if (ws.readyState === 1) ws.send(msg);
    }
  }

  return {
    wss,
    port: wss.address().port,
    broadcastRevocation,
    getPublicKeyBytes: () => pubKeyBytes,
    close: () => wss.close(),
  };
}

function runRevokePropagationTest() {
  return new Promise((resolve, reject) => {
    const server = createMockRevocationServer();
    const targetTokenId = 'propagation-test-token-123';
    const revoked = new Set();

    const client = new (require('ws'))(`ws://127.0.0.1:${server.port}`);

    client.on('open', () => {
      server.broadcastRevocation(targetTokenId);
    });

    client.on('message', (data) => {
      try {
        const payload = JSON.parse(data.toString());
        if (payload.event === 'revoked' && payload.token_id) {
          const valid = verifyRevocationPayload(payload, server.getPublicKeyBytes());
          if (valid) revoked.add(payload.token_id);
        }
      } catch (_) {}
    });

    client.on('error', (err) => {
      server.close();
      reject(err);
    });

    setTimeout(() => {
      client.close();
      server.close();
      const ok = revoked.has(targetTokenId);
      resolve({ ok, msg: 'Revoke propagation: client receives and verifies signed revocation' });
    }, 500);
  });
}

module.exports = { runRevokePropagationTest };
