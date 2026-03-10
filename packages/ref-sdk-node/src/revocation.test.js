'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');
const { verifyRevocationPayload } = require('./revocation.js');

function signRevocation(tokenId, ts, nonce) {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const payload = { token_id: tokenId, event: 'revoked', ts, nonce };
  const canonical = JSON.stringify({
    event: payload.event,
    nonce: payload.nonce,
    token_id: payload.token_id,
    ts: payload.ts,
  });
  const sig = crypto.sign(null, Buffer.from(canonical, 'utf8'), privateKey);
  return {
    payload: { ...payload, kid: 'revocation', signature: sig.toString('base64') },
    publicKey,
  };
}

describe('verifyRevocationPayload', () => {
  it('verifies valid signed payload (conformance 10)', () => {
    const ts = new Date().toISOString();
    const nonce = crypto.randomUUID();
    const { payload, publicKey } = signRevocation('token-123', ts, nonce);
    assert.strictEqual(verifyRevocationPayload(payload, publicKey), true);
  });

  it('rejects stale payload (conformance 11)', () => {
    const old = new Date(Date.now() - 130 * 1000).toISOString();
    const { payload, publicKey } = signRevocation('t', old, crypto.randomUUID());
    assert.strictEqual(verifyRevocationPayload(payload, publicKey), false);
  });

  it('rejects tampered payload (conformance 12)', () => {
    const ts = new Date().toISOString();
    const { payload, publicKey } = signRevocation('token-123', ts, crypto.randomUUID());
    payload.token_id = 'tampered';
    assert.strictEqual(verifyRevocationPayload(payload, publicKey), false);
  });

  it('rejects without public key', () => {
    const ts = new Date().toISOString();
    const { payload } = signRevocation('t', ts, crypto.randomUUID());
    assert.strictEqual(verifyRevocationPayload(payload, null), false);
  });
});
