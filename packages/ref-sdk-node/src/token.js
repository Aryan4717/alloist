'use strict';

const { createLocalJWKSet, jwtVerify } = require('jose');

/**
 * Verify ACT-lite JWT with JWKS.
 * @param {string} token - JWT string
 * @param {object} jwks - JWKS object { keys: [...] }
 * @returns {{ valid: true, jti: string, scopes: string[], subject: string } | { valid: false, reason: string }}
 */
async function verifyToken(token, jwks) {
  const JWKS = createLocalJWKSet(jwks);
  try {
    const { payload } = await jwtVerify(token, JWKS, {
      algorithms: ['EdDSA'],
      clockTolerance: 5,
    });
    const exp = payload.exp;
    if (exp && exp < Math.floor(Date.now() / 1000)) {
      return { valid: false, reason: 'token_expired' };
    }
    return {
      valid: true,
      jti: payload.jti || '',
      scopes: payload.scopes || [],
      subject: payload.sub || '',
    };
  } catch (err) {
    if (err.code === 'ERR_JWT_EXPIRED') {
      return { valid: false, reason: 'token_expired' };
    }
    if (err.code === 'ERR_JWS_SIGNATURE_VERIFICATION_FAILED') {
      return { valid: false, reason: 'invalid_signature' };
    }
    if (err.code === 'ERR_JWKS_NO_MATCHING_KEY' || err.message?.includes('kid')) {
      return { valid: false, reason: 'key_not_found' };
    }
    return { valid: false, reason: err.message || 'invalid_token' };
  }
}

module.exports = { verifyToken };
