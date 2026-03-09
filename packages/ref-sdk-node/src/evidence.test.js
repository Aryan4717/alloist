'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');
const { verifyEvidenceBundle } = require('./evidence.js');

function _canonical(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(_canonical).join(',') + ']';
  return '{' + Object.keys(obj).sort().map((k) => JSON.stringify(k) + ':' + _canonical(obj[k])).join(',') + '}';
}

function signBundle(bundle) {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const data = { ...bundle };
  delete data.runtime_signature;
  delete data.public_key;
  const payload = _canonical(data);
  const sig = crypto.sign(null, Buffer.from(payload, 'utf8'), privateKey);
  const jwk = publicKey.export({ format: 'jwk' });
  const raw = Buffer.from(jwk.x, 'base64url');
  const publicKeyB64 = raw.toString('base64');
  return {
    ...data,
    runtime_signature: sig.toString('base64'),
    public_key: publicKeyB64,
  };
}

describe('verifyEvidenceBundle', () => {
  it('verifies valid signed bundle (conformance 6)', () => {
    const bundle = {
      evidence_id: 'e1',
      action_name: 'gmail.send',
      token_snapshot: { jti: 't1' },
      timestamp: '2026-01-09T12:00:00',
      result: 'deny',
      runtime_metadata: {},
    };
    const signed = signBundle(bundle);
    assert.strictEqual(verifyEvidenceBundle(signed), true);
  });

  it('rejects tampered bundle (conformance 7)', () => {
    const bundle = {
      evidence_id: 'e1',
      action_name: 'gmail.send',
      token_snapshot: {},
      timestamp: '2026-01-09T12:00:00',
      result: 'deny',
      runtime_metadata: {},
    };
    const signed = signBundle(bundle);
    signed.action_name = 'tampered';
    assert.strictEqual(verifyEvidenceBundle(signed), false);
  });

  it('verifies input_hash when present (conformance 8)', () => {
    const excerpt = { action_name: 'a', token_snapshot: {}, metadata: {} };
    const inputHash = crypto.createHash('sha256').update(_canonical(excerpt)).digest('hex');
    const bundle = {
      evidence_id: 'e1',
      action_name: 'a',
      token_snapshot: {},
      timestamp: '2026-01-09T12:00:00',
      input_hash: inputHash,
      result: 'deny',
      runtime_metadata: {},
    };
    const signed = signBundle(bundle);
    assert.strictEqual(verifyEvidenceBundle(signed), true);
  });

  it('rejects missing runtime_signature', () => {
    const bundle = { evidence_id: 'e1', action_name: 'a', public_key: 'dGVzdA==' };
    assert.strictEqual(verifyEvidenceBundle(bundle), false);
  });
});
