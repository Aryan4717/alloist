'use strict';

const crypto = require('crypto');

function _canonicalJson(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(_canonicalJson).join(',') + ']';
  const keys = Object.keys(obj).sort();
  const parts = keys.map((k) => JSON.stringify(k) + ':' + _canonicalJson(obj[k]));
  return '{' + parts.join(',') + '}';
}

function _toBase64Url(buf) {
  return buf.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Verify signed evidence bundle per ACT-lite spec.
 * @param {object} bundle - Evidence bundle (must include runtime_signature, public_key)
 * @returns {boolean}
 */
function verifyEvidenceBundle(bundle) {
  const data = { ...bundle };
  const runtimeSignature = data.runtime_signature;
  const publicKeyB64 = data.public_key || data.publicKey;

  if (!runtimeSignature) return false;
  if (!publicKeyB64) return false;

  delete data.runtime_signature;
  delete data.runtimeSignature;
  delete data.public_key;
  delete data.publicKey;

  const payloadStr = _canonicalJson(data);
  const payloadBytes = Buffer.from(payloadStr, 'utf8');

  let publicKey;
  try {
    const raw = Buffer.from(publicKeyB64, 'base64');
    const x = _toBase64Url(raw);
    publicKey = crypto.createPublicKey({
      key: { kty: 'OKP', crv: 'Ed25519', x },
      format: 'jwk',
    });
  } catch {
    return false;
  }

  const sig = Buffer.from(runtimeSignature, 'base64');
  try {
    if (!crypto.verify(null, payloadBytes, publicKey, sig)) return false;
  } catch {
    return false;
  }

  const inputHash = data.input_hash;
  if (inputHash) {
    const excerpt = {
      action_name: data.action_name || '',
      token_snapshot: data.token_snapshot || {},
      metadata: data.runtime_metadata || {},
    };
    const computed = crypto.createHash('sha256').update(_canonicalJson(excerpt)).digest('hex');
    if (computed !== inputHash) return false;
  }

  return true;
}

module.exports = { verifyEvidenceBundle };
