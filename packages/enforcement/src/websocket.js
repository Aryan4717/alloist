'use strict';

const WebSocket = require('ws');
const { fetchRevocationPublicKey, verifyRevocationPayload } = require('./revocationVerify.js');

const HEARTBEAT_INTERVAL_MS = 30000;

function createRevocationListener(apiUrl, onRevoked) {
  const wsUrl = apiUrl.replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/revocations';
  const httpBase = apiUrl.replace(/\/$/, '').replace(/^ws:\/\//, 'http://').replace(/^wss:\/\//, 'https://');

  let ws = null;
  let reconnectTimeout = null;
  let heartbeatInterval = null;
  let backoff = 1000;
  const maxBackoff = 30000;

  function connect() {
    try {
      ws = new WebSocket(wsUrl);
      ws.on('message', async (data) => {
        try {
          const msg = JSON.parse(data.toString());
          if (msg.type === 'pong') {
            return;
          }
          if (msg.event !== 'revoked' || !msg.token_id) return;

          const tokenId = msg.token_id;
          if (msg.signature) {
            const pubKey = await fetchRevocationPublicKey(httpBase);
            if (!verifyRevocationPayload(msg, pubKey)) return;
          }
          onRevoked(tokenId);
        } catch {
          // ignore parse errors
        }
      });
      ws.on('close', () => {
        ws = null;
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
          heartbeatInterval = null;
        }
        const delay = Math.min(backoff, maxBackoff);
        const jitter = delay * (0.5 + Math.random());
        backoff = Math.min(backoff * 2, maxBackoff);
        reconnectTimeout = setTimeout(connect, jitter);
      });
      ws.on('open', () => {
        backoff = 1000;
        heartbeatInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            try {
              ws.send(JSON.stringify({ type: 'ping' }));
            } catch {
              // ignore
            }
          }
        }, HEARTBEAT_INTERVAL_MS);
      });
      ws.on('error', () => {
        // connection will close, reconnect will trigger
      });
    } catch {
      reconnectTimeout = setTimeout(connect, backoff);
    }
  }

  connect();

  return {
    close() {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (heartbeatInterval) clearInterval(heartbeatInterval);
      if (ws) ws.close();
    },
  };
}

module.exports = { createRevocationListener };
