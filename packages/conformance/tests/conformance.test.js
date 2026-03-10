'use strict';

/**
 * ACT-lite conformance tests.
 * Maps to spec/CONFORMANCE.md tests 1-12.
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');
const {
  verifyToken,
  verifyEvidenceBundle,
  verifyRevocationPayload,
} = require('@alloist/ref-sdk-node');

const FIXTURES = path.join(__dirname, '..', 'fixtures');

function loadFixture(name) {
  const p = path.join(FIXTURES, name);
  if (!fs.existsSync(p)) return null;
  const content = fs.readFileSync(p, 'utf8');
  if (name.endsWith('.json')) return JSON.parse(content);
  return content.trim();
}

async function runConformanceTests() {
  const results = [];
  const jwks = loadFixture('jwks.json');
  const validToken = loadFixture('valid_token.jwt');
  const expiredToken = loadFixture('expired_token.jwt');
  const tamperedToken = loadFixture('tampered_token.jwt');
  const validBundle = loadFixture('valid_evidence_bundle.json');
  const tamperedBundle = loadFixture('tampered_evidence_bundle.json');
  const validRevocation = loadFixture('valid_revocation_payload.json');
  const staleRevocation = loadFixture('stale_revocation_payload.json');
  const tamperedRevocation = loadFixture('tampered_revocation_payload.json');
  const revPubKeyB64 = loadFixture('revocation_public_key.txt');
  const revPubKey = revPubKeyB64 ? Buffer.from(revPubKeyB64, 'base64') : null;

  if (!jwks || !validToken) {
    return { ok: false, error: 'Run npm run generate first' };
  }

  try {
    const r1 = await verifyToken(validToken, jwks);
    results.push({ n: 1, ok: r1.valid === true, msg: 'Valid token verifies' });
  } catch (e) {
    results.push({ n: 1, ok: false, msg: e.message });
  }

  try {
    const r2 = await verifyToken(expiredToken, jwks);
    results.push({ n: 2, ok: r2.valid === false && r2.reason === 'token_expired', msg: 'Expired token rejected' });
  } catch (e) {
    results.push({ n: 2, ok: false, msg: e.message });
  }

  try {
    const r3 = await verifyToken(tamperedToken, jwks);
    results.push({ n: 3, ok: r3.valid === false, msg: 'Tampered signature rejected' });
  } catch (e) {
    results.push({ n: 3, ok: false, msg: e.message });
  }

  try {
    const jwksNoKid = { keys: [{ ...jwks.keys[0], kid: 'wrong-kid' }] };
    const r4 = await verifyToken(validToken, jwksNoKid);
    results.push({ n: 4, ok: r4.valid === false, msg: 'Unknown kid rejected' });
  } catch (e) {
    results.push({ n: 4, ok: false, msg: e.message });
  }

  try {
    const hasOkp = jwks.keys.some((k) => k.kty === 'OKP' && k.crv === 'Ed25519' && k.kid);
    results.push({ n: 5, ok: hasOkp, msg: 'JWKS format' });
  } catch (e) {
    results.push({ n: 5, ok: false, msg: e.message });
  }

  try {
    results.push({ n: 6, ok: verifyEvidenceBundle(validBundle), msg: 'Signed bundle verifies' });
  } catch (e) {
    results.push({ n: 6, ok: false, msg: e.message });
  }

  try {
    results.push({ n: 7, ok: !verifyEvidenceBundle(tamperedBundle), msg: 'Tampered bundle rejected' });
  } catch (e) {
    results.push({ n: 7, ok: false, msg: e.message });
  }

  try {
    const hasInputHash = validBundle && validBundle.input_hash;
    results.push({ n: 8, ok: hasInputHash && verifyEvidenceBundle(validBundle), msg: 'input_hash matches' });
  } catch (e) {
    results.push({ n: 8, ok: false, msg: e.message });
  }

  const required = ['evidence_id', 'action_name', 'token_snapshot', 'timestamp', 'input_hash', 'result', 'runtime_signature', 'public_key'];
  try {
    const hasAll = required.every((f) => validBundle && validBundle[f] !== undefined);
    results.push({ n: 9, ok: hasAll, msg: 'Required fields present' });
  } catch (e) {
    results.push({ n: 9, ok: false, msg: e.message });
  }

  try {
    results.push({ n: 10, ok: revPubKey && verifyRevocationPayload(validRevocation, revPubKey), msg: 'Signed revocation verifies' });
  } catch (e) {
    results.push({ n: 10, ok: false, msg: e.message });
  }

  try {
    results.push({ n: 11, ok: !verifyRevocationPayload(staleRevocation, revPubKey), msg: 'Stale payload rejected' });
  } catch (e) {
    results.push({ n: 11, ok: false, msg: e.message });
  }

  try {
    results.push({ n: 12, ok: !verifyRevocationPayload(tamperedRevocation, revPubKey), msg: 'Tampered payload rejected' });
  } catch (e) {
    results.push({ n: 12, ok: false, msg: e.message });
  }

  return { ok: results.every((r) => r.ok), results };
}

module.exports = { runConformanceTests };
