'use strict';

const { SignJWT, generateKeyPair, exportJWK } = require('jose');

async function makeTestToken(payload = {}, kid = 'test-key-1') {
  const { publicKey, privateKey } = await generateKeyPair('EdDSA', {
    crv: 'Ed25519',
    kid,
  });

  const now = Math.floor(Date.now() / 1000);
  const jti = payload.jti || 'test-jti-123';
  const token = await new SignJWT({
    sub: payload.sub || 'test-user',
    scopes: payload.scopes || ['email:send'],
    jti,
    ...payload,
  })
    .setProtectedHeader({ alg: 'EdDSA', typ: 'JWT', kid })
    .setIssuedAt(now)
    .setExpirationTime(now + 3600)
    .sign(privateKey);

  const jwk = await exportJWK(publicKey);
  const jwks = { keys: [{ ...jwk, kid, alg: 'EdDSA' }] };

  return { token, jwks, jti };
}

module.exports = { makeTestToken };
