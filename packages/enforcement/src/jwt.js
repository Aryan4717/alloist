'use strict';

const { createRemoteJWKSet, createLocalJWKSet, jwtVerify } = require('jose');

async function verifyTokenLocally(token, apiUrl, jwksOverride = null) {
  const JWKS = jwksOverride
    ? createLocalJWKSet(jwksOverride)
    : createRemoteJWKSet(new URL(`${apiUrl.replace(/\/$/, '')}/keys`));

  try {
    const { payload } = await jwtVerify(token, JWKS, {
      algorithms: ['EdDSA'],
      clockTolerance: 5,
    });

    const exp = payload.exp;
    if (exp && exp < Math.floor(Date.now() / 1000)) {
      return { valid: false, reason: 'token_expired' };
    }

    const jti = payload.jti || '';
    const scopes = payload.scopes || [];
    return { valid: true, jti, scopes, subject: payload.sub };
  } catch (err) {
    if (err.code === 'ERR_JWT_EXPIRED') {
      return { valid: false, reason: 'token_expired' };
    }
    if (err.code === 'ERR_JWS_SIGNATURE_VERIFICATION_FAILED') {
      return { valid: false, reason: 'invalid_signature' };
    }
    return { valid: false, reason: err.message || 'invalid_token' };
  }
}

module.exports = { verifyTokenLocally };
