#!/usr/bin/env node
'use strict';

/**
 * Generate conformance test fixtures.
 * Writes to fixtures/ directory.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { SignJWT, generateKeyPair, exportJWK } = require('jose');

const FIXTURES_DIR = path.join(__dirname, '..', 'fixtures');

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function _canonical(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(_canonical).join(',') + ']';
  return '{' + Object.keys(obj).sort().map((k) => JSON.stringify(k) + ':' + _canonical(obj[k])).join(',') + '}';
}

async function main() {
  ensureDir(FIXTURES_DIR);

  const { publicKey: josePub, privateKey: josePriv } = await generateKeyPair('EdDSA', { crv: 'Ed25519', kid: 'conformance-key' });
  const jwk = await exportJWK(josePub);
  const jwks = { keys: [{ ...jwk, kid: 'conformance-key', alg: 'EdDSA' }] };
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  fs.writeFileSync(path.join(FIXTURES_DIR, 'jwks.json'), JSON.stringify(jwks, null, 2));

  const now = Math.floor(Date.now() / 1000);
  const validToken = await new SignJWT({
    sub: 'conformance-user',
    scopes: ['read', 'write'],
    jti: 'conformance-jti-1',
    iat: now,
    exp: now + 3600,
  })
    .setProtectedHeader({ alg: 'EdDSA', typ: 'JWT', kid: 'conformance-key' })
    .setIssuedAt(now)
    .setExpirationTime(now + 3600)
    .sign(josePriv);
  fs.writeFileSync(path.join(FIXTURES_DIR, 'valid_token.jwt'), validToken);

  const expiredToken = await new SignJWT({
    sub: 'conformance-user',
    scopes: ['read'],
    jti: 'conformance-jti-expired',
    iat: now - 7200,
    exp: now - 3600,
  })
    .setProtectedHeader({ alg: 'EdDSA', typ: 'JWT', kid: 'conformance-key' })
    .setIssuedAt(now - 7200)
    .setExpirationTime(now - 3600)
    .sign(josePriv);
  fs.writeFileSync(path.join(FIXTURES_DIR, 'expired_token.jwt'), expiredToken);

  const [h, p, s] = validToken.split('.');
  fs.writeFileSync(path.join(FIXTURES_DIR, 'tampered_token.jwt'), `${h}.${p}.${s.slice(0, -2)}xx`);

  const bundle = {
    evidence_id: 'conformance-evidence-1',
    action_name: 'gmail.send',
    token_snapshot: { jti: 't1' },
    timestamp: '2026-01-09T12:00:00',
    result: 'deny',
    runtime_metadata: {},
  };
  const excerpt = { action_name: bundle.action_name, token_snapshot: bundle.token_snapshot, metadata: bundle.runtime_metadata };
  bundle.input_hash = crypto.createHash('sha256').update(_canonical(excerpt)).digest('hex');
  const payloadStr = _canonical(bundle);
  const sig = crypto.sign(null, Buffer.from(payloadStr, 'utf8'), privateKey);
  const pubRaw = publicKey.export({ format: 'jwk' });
  const raw = Buffer.from(pubRaw.x, 'base64url');
  const validBundle = {
    ...bundle,
    runtime_signature: sig.toString('base64'),
    public_key: raw.toString('base64'),
  };
  fs.writeFileSync(path.join(FIXTURES_DIR, 'valid_evidence_bundle.json'), JSON.stringify(validBundle, null, 2));

  const tamperedBundle = { ...validBundle, action_name: 'tampered' };
  fs.writeFileSync(path.join(FIXTURES_DIR, 'tampered_evidence_bundle.json'), JSON.stringify(tamperedBundle, null, 2));

  const revPayload = {
    token_id: 'conformance-revoke-1',
    event: 'revoked',
    ts: new Date().toISOString(),
    nonce: crypto.randomUUID(),
  };
  const revCanonical = JSON.stringify({ event: revPayload.event, nonce: revPayload.nonce, token_id: revPayload.token_id, ts: revPayload.ts });
  const revSig = crypto.sign(null, Buffer.from(revCanonical, 'utf8'), privateKey);
  const validRevocation = { ...revPayload, kid: 'revocation', signature: revSig.toString('base64') };
  fs.writeFileSync(path.join(FIXTURES_DIR, 'valid_revocation_payload.json'), JSON.stringify(validRevocation, null, 2));

  const staleRevPayload = {
    token_id: 'conformance-revoke-stale',
    event: 'revoked',
    ts: new Date(Date.now() - 130 * 1000).toISOString(),
    nonce: crypto.randomUUID(),
  };
  const staleCanonical = JSON.stringify({ event: staleRevPayload.event, nonce: staleRevPayload.nonce, token_id: staleRevPayload.token_id, ts: staleRevPayload.ts });
  const staleSig = crypto.sign(null, Buffer.from(staleCanonical, 'utf8'), privateKey);
  const staleRevocation = { ...staleRevPayload, kid: 'revocation', signature: staleSig.toString('base64') };
  fs.writeFileSync(path.join(FIXTURES_DIR, 'stale_revocation_payload.json'), JSON.stringify(staleRevocation, null, 2));

  const tamperedRevocation = { ...validRevocation, token_id: 'tampered' };
  fs.writeFileSync(path.join(FIXTURES_DIR, 'tampered_revocation_payload.json'), JSON.stringify(tamperedRevocation, null, 2));

  const revPubKey = raw.toString('base64');
  fs.writeFileSync(path.join(FIXTURES_DIR, 'revocation_public_key.txt'), revPubKey);

  console.log('Fixtures generated in', FIXTURES_DIR);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
