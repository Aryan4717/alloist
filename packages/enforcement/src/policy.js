'use strict';

// action.name -> required scope (e.g. send_email -> email:send)
const ACTION_SCOPE_MAP = {
  send_email: 'email:send',
  delete_user: 'user:delete',
  transfer_funds: 'funds:transfer',
};

function checkPolicy(action, scopes) {
  if (!action?.name) {
    return { allowed: true };
  }

  const requiredScope = ACTION_SCOPE_MAP[action.name];
  if (!requiredScope) {
    return { allowed: true };
  }

  const hasScope = Array.isArray(scopes) && scopes.includes(requiredScope);
  if (!hasScope) {
    return {
      allowed: false,
      reason: `missing_scope:${requiredScope}`,
    };
  }

  return { allowed: true };
}

module.exports = { checkPolicy };
