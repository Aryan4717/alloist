const DEFAULT_BACKEND = "http://localhost:8001";
const WS_PATH = "/consent/ws";
const DECISION_PATH = "/consent/decision";

let ws: WebSocket | null = null;
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let backoff = 1000;
const maxBackoff = 30000;

interface ConsentRequest {
  type: string;
  request_id: string;
  agent_name: string;
  action: { service: string; name: string; metadata?: Record<string, unknown> };
  metadata?: Record<string, unknown>;
  risk_level: string;
}

function getWsUrl(base: string): string {
  const url = base.replace(/^http/, "ws").replace(/\/$/, "");
  return `${url}${WS_PATH}`;
}

function connect(): void {
  chrome.storage.local.get(["backendUrl"], (result) => {
    const base = result.backendUrl || DEFAULT_BACKEND;
    const wsUrl = getWsUrl(base);
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data as string);
          if (msg.type === "pong") return;
          if (msg.type === "consent_request") {
            (globalThis as unknown as { _pending?: ConsentRequest })._pending = msg;
            chrome.runtime.sendMessage({ type: "CONSENT_REQUEST", payload: msg }).catch(() => {});
          }
        } catch {
          // ignore parse errors
        }
      };
      ws.onclose = () => {
        ws = null;
        const delay = Math.min(backoff, maxBackoff);
        backoff = Math.min(backoff * 2, maxBackoff);
        reconnectTimeout = setTimeout(connect, delay);
      };
      ws.onopen = () => {
        backoff = 1000;
      };
      ws.onerror = () => {};
    } catch {
      reconnectTimeout = setTimeout(connect, 1000);
    }
  });
}

function sendPing(): void {
  if (ws && ws.readyState === WebSocket.OPEN) {
    try {
      ws.send(JSON.stringify({ type: "ping" }));
    } catch {
      // ignore
    }
  }
}

chrome.runtime.onMessage.addListener(
  (
    message: { type: string; request_id?: string; decision?: string; org_id?: string },
    _sender,
    sendResponse
  ) => {
    if (message.type === "SUBMIT_DECISION" && message.request_id && message.decision) {
      chrome.storage.local.get(["backendUrl", "apiKey", "orgId"], async (result) => {
        const base = result.backendUrl || DEFAULT_BACKEND;
        const apiKey = result.apiKey || "dev-api-key";
        const orgId = result.orgId || "00000000-0000-0000-0000-000000000001";
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          "X-API-Key": apiKey,
          "X-Org-Id": orgId,
        };
        try {
          const res = await fetch(`${base.replace(/\/$/, "")}${DECISION_PATH}`, {
            method: "POST",
            headers,
            body: JSON.stringify({
              request_id: message.request_id,
              decision: message.decision,
            }),
          });
          if (res.ok) {
            sendResponse({ ok: true });
          } else {
            sendResponse({ ok: false, error: await res.text() });
          }
        } catch (err) {
          sendResponse({ ok: false, error: String(err) });
        }
      });
      return true; // async response
    }
    if (message.type === "GET_PENDING") {
      sendResponse({ pending: (globalThis as unknown as { _pending?: ConsentRequest })._pending ?? null });
      return false;
    }
    if (message.type === "CLEAR_PENDING") {
      (globalThis as unknown as { _pending?: ConsentRequest })._pending = undefined;
      sendResponse({});
      return false;
    }
    return false;
  }
);

connect();
setInterval(sendPing, 30000);
