'use strict';

const crypto = require('crypto');

const REVOCATION_KID = 'revocation';
const MAX_AGE_SECONDS = 120;
const CACHE_TTL_MS = 5 * 60 * 1000;

let cachedKey = null;
let cachedAt = 0;

function canonicalPayload(data) {
  return JSON.stringify({
    event: data.event,
    nonce: data.nonce,
    token_id: data.token_id,
    ts: data.ts,
  });
}

/**
 * Verify signed revocation payload.
 * @param {object} payload - { token_id, event, ts, nonce, kid, signature }
 * @param {crypto.KeyObject|Buffer} publicKey - Ed25519 public key (KeyObject or raw 32 bytes)
 * @returns {boolean}
 */
function verifyRevocationPayload(payload, publicKey) {
  if (!publicKey) return false;

  const signatureB64 = payload.signature;
  const kid = payload.kid;
  if (!signatureB64 || kid !== REVOCATION_KID) return false;

  const tsStr = payload.ts;
  if (!tsStr) return false;

  try {
    const ts = new Date(tsStr.replace('Z', '+00:00'));
    const age = (Date.now() - ts.getTime()) / 1000;
    if (age < 0 || age > MAX_AGE_SECONDS) return false;
  } catch {
    return false;
  }

  const verifyPayload = canonicalPayload(payload);
  const signature = Buffer.from(signatureB64, 'base64');

  let keyObj = publicKey;
  if (Buffer.isBuffer(publicKey)) {
    const x = publicKey.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    keyObj = crypto.createPublicKey({
      key: { kty: 'OKP', crv: 'Ed25519', x },
      format: 'jwk',
    });
  }

  try {
    return crypto.verify(null, Buffer.from(verifyPayload, 'utf8'), keyObj, signature);
  } catch {
    return false;
  }
}

/**
 * Fetch revocation public key from GET /keys.
 * @param {string} apiUrl - Base URL (e.g. http://localhost:8000)
 * @returns {Promise<crypto.KeyObject|null>}
 */
async function fetchRevocationPublicKey(apiUrl) {
  const now = Date.now();
  if (cachedKey && now - cachedAt < CACHE_TTL_MS) return cachedKey;

  const base = apiUrl.replace(/\/$/, '').replace(/^ws:\/\//, 'http://').replace(/^wss:\/\//, 'https://');
  const url = `${base}/keys`;

  try {
    const res = await fetch(url);
    if (!res.ok) return cachedKey;
    const data = await res.json();
    for (const key of data.keys || []) {
      if (key.kid === REVOCATION_KID && key.x) {
        cachedKey = crypto.createPublicKey({
          key: { kty: 'OKP', crv: 'Ed25519', x: key.x },
          format: 'jwk',
        });
        cachedAt = now;
        return cachedKey;
      }
    }
    return cachedKey;
  } catch {
    return cachedKey;
  }
}

module.exports = {
  verifyRevocationPayload,
  fetchRevocationPublicKey,
};
