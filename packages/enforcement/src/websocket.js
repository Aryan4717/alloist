'use strict';

const WebSocket = require('ws');

function createRevocationListener(apiUrl, onRevoked) {
  const wsUrl = apiUrl.replace(/^http/, 'ws').replace(/\/$/, '') + '/ws/revocations';
  let ws = null;
  let reconnectTimeout = null;
  let backoff = 1000;
  const maxBackoff = 30000;

  function connect() {
    try {
      ws = new WebSocket(wsUrl);
      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data.toString());
          if (msg.event === 'revoked' && msg.token_id) {
            onRevoked(msg.token_id);
          }
        } catch {
          // ignore parse errors
        }
      });
      ws.on('close', () => {
        ws = null;
        reconnectTimeout = setTimeout(() => {
          backoff = Math.min(backoff * 2, maxBackoff);
          connect();
        }, backoff);
      });
      ws.on('open', () => {
        backoff = 1000;
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
      if (ws) ws.close();
    },
  };
}

module.exports = { createRevocationListener };
