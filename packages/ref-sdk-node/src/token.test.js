'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { SignJWT, generateKeyPair, exportJWK } = require('jose');
const { verifyToken } = require('./token.js');

async function makeToken(payload = {}, kid = 'test-key-1') {
  const { publicKey, privateKey } = await generateKeyPair('EdDSA', { crv: 'Ed25519', kid });
  const now = Math.floor(Date.now() / 1000);
  const jti = payload.jti || 'test-jti';
  const token = await new SignJWT({
    sub: payload.sub || 'user',
    scopes: payload.scopes || ['read'],
    jti,
    ...payload,
  })
    .setProtectedHeader({ alg: 'EdDSA', typ: 'JWT', kid })
    .setIssuedAt(now)
    .setExpirationTime(payload.exp ?? now + 3600)
    .sign(privateKey);
  const jwk = await exportJWK(publicKey);
  const jwks = { keys: [{ ...jwk, kid, alg: 'EdDSA' }] };
  return { token, jwks, jti };
}

describe('verifyToken', () => {
  it('verifies valid token (conformance 1)', async () => {
    const { token, jwks } = await makeToken();
    const r = await verifyToken(token, jwks);
    assert.strictEqual(r.valid, true);
    assert.strictEqual(r.jti, 'test-jti');
    assert.deepStrictEqual(r.scopes, ['read']);
    assert.strictEqual(r.subject, 'user');
  });

  it('rejects expired token (conformance 2)', async () => {
    const now = Math.floor(Date.now() / 1000);
    const { token, jwks } = await makeToken({ exp: now - 60 });
    const r = await verifyToken(token, jwks);
    assert.strictEqual(r.valid, false);
    assert.strictEqual(r.reason, 'token_expired');
  });

  it('rejects tampered token (conformance 3)', async () => {
    const { token, jwks } = await makeToken();
    const [h, p, s] = token.split('.');
    const tampered = `${h}.${p}.${s.slice(0, -2)}xx`;
    const r = await verifyToken(tampered, jwks);
    assert.strictEqual(r.valid, false);
    assert.strictEqual(r.reason, 'invalid_signature');
  });

  it('rejects unknown kid (conformance 4)', async () => {
    const { token, jwks } = await makeToken({}, 'key-a');
    const jwksWrong = { keys: [{ ...jwks.keys[0], kid: 'key-b' }] };
    const r = await verifyToken(token, jwksWrong);
    assert.strictEqual(r.valid, false);
    assert.ok(r.reason === 'key_not_found' || r.reason?.includes('key'));
  });

  it('accepts JWKS with OKP Ed25519 kid (conformance 5)', async () => {
    const { token, jwks } = await makeToken();
    assert.ok(jwks.keys[0].kty === 'OKP' || jwks.keys[0].kty === 'OKP');
    assert.ok(jwks.keys[0].crv === 'Ed25519');
    assert.ok(jwks.keys[0].kid);
    const r = await verifyToken(token, jwks);
    assert.strictEqual(r.valid, true);
  });
});
