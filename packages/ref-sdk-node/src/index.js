'use strict';

const { verifyToken } = require('./token.js');
const { verifyEvidenceBundle } = require('./evidence.js');
const { verifyRevocationPayload, fetchRevocationPublicKey } = require('./revocation.js');

module.exports = {
  verifyToken,
  verifyEvidenceBundle,
  verifyRevocationPayload,
  fetchRevocationPublicKey,
};
