'use strict';

const { randomUUID } = require('crypto');
const { createRevocationListener } = require('./websocket.js');
const { verifyTokenLocally } = require('./jwt.js');
const { validateTokenRemote } = require('./api.js');
const { checkPolicy } = require('./policy.js');

function resolveFailMode(actionName, failMode, failModePerAction, failClosed, highRiskActions) {
  if (failModePerAction != null && actionName in failModePerAction) {
    return failModePerAction[actionName];
  }
  if (failModePerAction != null) {
    return failMode;
  }
  if (failClosed && highRiskActions.includes(actionName)) {
    return 'fail_closed';
  }
  return 'fail_open';
}

function createEnforcement(options = {}) {
  const {
    apiUrl = 'http://localhost:8000',
    apiKey = '',
    failClosed = false,
    highRiskActions = ['send_email', 'delete_user', 'transfer_funds'],
    failMode = 'fail_open',
    failModePerAction = null,
    onLog = null,
    jwksOverride = null, // for testing: pass { keys: [...] } to bypass fetch
    _testRevokedTokens = null, // for testing: shared set to inject revocations
  } = options;

  const revokedTokens = _testRevokedTokens || new Set();
  const cache = new Map(); // jti -> { status, subject, scopes, cachedAt }

  const ws = createRevocationListener(apiUrl, (tokenId) => {
    revokedTokens.add(tokenId);
    if (onLog) onLog({ type: 'revocation', token_id: tokenId });
  });

  return {
    async check({ token, action }) {
      const evidenceId = randomUUID();
      const log = (payload) => {
        if (onLog) onLog({ evidence_id: evidenceId, ...payload });
      };

      try {
        // 1. Local validation: signature + TTL
        const local = await verifyTokenLocally(token, apiUrl, jwksOverride);
        if (!local.valid) {
          log({ action, result: 'blocked', reason: local.reason });
          return { allowed: false, reason: local.reason, evidence_id: evidenceId };
        }

        const { jti, scopes } = local;

        // 2. Revocation cache
        if (revokedTokens.has(jti)) {
          log({ action, result: 'blocked', reason: 'token_revoked' });
          return { allowed: false, reason: 'token_revoked', evidence_id: evidenceId };
        }

        // 3. Remote fallback if not cached
        let status = cache.get(jti)?.status;
        if (status === undefined) {
          const remote = await validateTokenRemote(token, apiUrl, apiKey);
          if (remote) {
            status = remote.status;
            cache.set(jti, {
              status: remote.status,
              subject: remote.subject,
              scopes: remote.scopes,
              cachedAt: Date.now(),
            });
            if (remote.status === 'revoked') {
              revokedTokens.add(jti);
              log({ action, result: 'blocked', reason: 'token_revoked' });
              return { allowed: false, reason: 'token_revoked', evidence_id: evidenceId };
            }
          } else {
            const mode = resolveFailMode(
              action?.name,
              failMode,
              failModePerAction,
              failClosed,
              highRiskActions,
            );
            if (mode === 'fail_closed') {
              log({ action, result: 'blocked', reason: 'fail_closed_backend_unreachable' });
              return {
                allowed: false,
                reason: 'fail_closed_backend_unreachable',
                evidence_id: evidenceId,
              };
            }
            if (mode === 'soft_fail') {
              log({ action, result: 'allowed', degraded_mode: 'soft_fail' });
            }
          }
        }

        // 4. Policy check
        const policy = checkPolicy(action, scopes);
        if (!policy.allowed) {
          log({ action, result: 'blocked', reason: policy.reason });
          return { allowed: false, reason: policy.reason, evidence_id: evidenceId };
        }

        // 5. Fail-closed: re-check revoked before returning allowed (in-flight revocation)
        if (revokedTokens.has(jti)) {
          log({ action, result: 'blocked', reason: 'token_revoked' });
          return { allowed: false, reason: 'token_revoked', evidence_id: evidenceId };
        }

        log({ action, result: 'allowed' });
        return { allowed: true, evidence_id: evidenceId };
      } catch (err) {
        const mode = resolveFailMode(
          action?.name,
          failMode,
          failModePerAction,
          failClosed,
          highRiskActions,
        );
        if (mode === 'fail_closed') {
          log({ action, result: 'blocked', reason: err.message });
          return {
            allowed: false,
            reason: err.message,
            evidence_id: evidenceId,
          };
        }
        throw err;
      }
    },

    close() {
      ws.close();
    },
  };
}

module.exports = { createEnforcement };
