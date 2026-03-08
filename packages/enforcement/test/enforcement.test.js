'use strict';

const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert');
const { validateTokenRemote } = require('../src/api.js');
const { checkPolicy } = require('../src/policy.js');
const { makeTestToken } = require('./fixtures/make-token.js');

describe('policy', () => {
  it('allows when scope present', () => {
    assert.strictEqual(checkPolicy({ name: 'send_email' }, ['email:send']).allowed, true);
  });

  it('blocks when scope missing', () => {
    const r = checkPolicy({ name: 'send_email' }, ['read']);
    assert.strictEqual(r.allowed, false);
    assert.ok(r.reason?.includes('email:send'));
  });

  it('allows unknown action', () => {
    assert.strictEqual(checkPolicy({ name: 'unknown_action' }, []).allowed, true);
  });
});

describe('validateTokenRemote', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('returns data when API returns valid token', async () => {
    globalThis.fetch = async () => ({
      ok: true,
      json: async () => ({
        valid: true,
        status: 'active',
        subject: 'user1',
        scopes: ['email:send'],
        jti: 'abc-123',
      }),
    });

    const remote = await validateTokenRemote('token', 'http://localhost:9999', '');
    assert.strictEqual(remote.valid, true);
    assert.strictEqual(remote.status, 'active');
    assert.deepStrictEqual(remote.scopes, ['email:send']);
  });

  it('returns revoked when API returns revoked', async () => {
    globalThis.fetch = async () => ({
      ok: true,
      json: async () => ({
        valid: false,
        status: 'revoked',
        subject: 'user1',
        scopes: [],
        jti: 'xyz',
      }),
    });

    const remote = await validateTokenRemote('token', 'http://localhost:9999', '');
    assert.strictEqual(remote.valid, false);
    assert.strictEqual(remote.status, 'revoked');
  });

  it('returns null when fetch fails', async () => {
    globalThis.fetch = async () => {
      throw new Error('network error');
    };

    const remote = await validateTokenRemote('token', 'http://localhost:9999', '');
    assert.strictEqual(remote, null);
  });
});

describe('enforcement.check', () => {
  let originalFetch;
  let originalWebSocket;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    originalWebSocket = globalThis.WebSocket;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    globalThis.WebSocket = originalWebSocket;
  });

  it('returns blocked for revoked token from API', async () => {
    const { token, jwks, jti } = await makeTestToken({ scopes: ['email:send'], jti: 'revoked-jti' });

    globalThis.fetch = async (url) => {
      const u = url.toString();
      if (u.includes('/validate')) {
        return {
          ok: true,
          json: async () => ({
            valid: false,
            status: 'revoked',
            subject: 'user',
            scopes: [],
            jti,
          }),
        };
      }
      return { ok: false };
    };

    globalThis.WebSocket = class {
      constructor() {
        this.on = () => {};
        this.close = () => {};
      }
    };

    const { createEnforcement } = require('../src/index.js');
    const enforcement = createEnforcement({
      apiUrl: 'http://localhost:9999',
      failClosed: false,
      jwksOverride: jwks,
    });

    const result = await enforcement.check({
      token,
      action: { name: 'send_email', service: 'email', metadata: {} },
    });

    enforcement.close();
    assert.strictEqual(result.allowed, false);
    assert.strictEqual(result.reason, 'token_revoked');
    assert.ok(result.evidence_id);
  });

  it('returns allowed for valid token with correct scope', async () => {
    const { token, jwks } = await makeTestToken({ scopes: ['email:send'] });

    globalThis.fetch = async (url) => {
      const u = url.toString();
      if (u.includes('/validate')) {
        return {
          ok: true,
          json: async () => ({
            valid: true,
            status: 'active',
            subject: 'user',
            scopes: ['email:send'],
            jti: 'test-jti-123',
          }),
        };
      }
      return { ok: false };
    };

    globalThis.WebSocket = class {
      constructor() {
        this.on = () => {};
        this.close = () => {};
      }
    };

    const { createEnforcement } = require('../src/index.js');
    const enforcement = createEnforcement({
      apiUrl: 'http://localhost:9999',
      failClosed: false,
      jwksOverride: jwks,
    });

    const result = await enforcement.check({
      token,
      action: { name: 'send_email', service: 'email', metadata: {} },
    });

    enforcement.close();
    assert.strictEqual(result.allowed, true);
    assert.ok(result.evidence_id);
  });
});
