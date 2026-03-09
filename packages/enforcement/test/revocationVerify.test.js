'use strict';

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');
const {
  fetchRevocationPublicKey,
  verifyRevocationPayload,
} = require('../src/revocationVerify.js');

describe('verifyRevocationPayload', () => {
  it('returns true for valid signed payload', () => {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
    const payload = {
      token_id: 't1',
      event: 'revoked',
      ts: new Date().toISOString(),
      nonce: 'abc-123',
    };
    // Must match canonicalPayload in revocationVerify.js (event, nonce, token_id, ts)
    const canonical = JSON.stringify({
      event: payload.event,
      nonce: payload.nonce,
      token_id: payload.token_id,
      ts: payload.ts,
    });
    const sig = crypto.sign(null, Buffer.from(canonical, 'utf8'), privateKey);
    payload.signature = sig.toString('base64');
    payload.kid = 'revocation';

    assert.strictEqual(verifyRevocationPayload(payload, publicKey), true);
  });

  it('returns false for tampered payload', () => {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
    const payload = {
      token_id: 't1',
      event: 'revoked',
      ts: new Date().toISOString(),
      nonce: 'abc-123',
    };
    const canonical = JSON.stringify({
      event: payload.event,
      nonce: payload.nonce,
      token_id: payload.token_id,
      ts: payload.ts,
    });
    const sig = crypto.sign(null, Buffer.from(canonical, 'utf8'), privateKey);
    payload.signature = sig.toString('base64');
    payload.kid = 'revocation';
    payload.token_id = 'tampered';

    assert.strictEqual(verifyRevocationPayload(payload, publicKey), false);
  });

  it('returns false when publicKey is null', () => {
    const payload = {
      token_id: 't1',
      event: 'revoked',
      ts: new Date().toISOString(),
      nonce: 'x',
      signature: 'YQ==',
      kid: 'revocation',
    };
    assert.strictEqual(verifyRevocationPayload(payload, null), false);
  });
});

describe('fetchRevocationPublicKey', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('returns key from JWKS when kid=revocation present', async () => {
    const { publicKey } = crypto.generateKeyPairSync('ed25519');
    const jwk = publicKey.export({ format: 'jwk' });

    globalThis.fetch = async () => ({
      ok: true,
      json: async () => ({
        keys: [{ ...jwk, kid: 'revocation' }],
      }),
    });

    const result = await fetchRevocationPublicKey('http://localhost:8000');
    assert.ok(result);
  });
});
