import { useEffect, useState } from "react";

interface ConsentRequest {
  request_id: string;
  agent_name: string;
  action: { service: string; name: string; metadata?: Record<string, unknown> };
  metadata?: Record<string, unknown>;
  risk_level: string;
}

export function App() {
  const [pending, setPending] = useState<ConsentRequest | null>(null);
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chrome.runtime.sendMessage({ type: "GET_PENDING" }, (res) => {
      setPending(res?.pending ?? null);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    const listener = (
      message: { type: string; payload?: ConsentRequest },
      _sender: unknown,
      sendResponse: (r: unknown) => void
    ) => {
      if (message.type === "CONSENT_REQUEST" && message.payload) {
        setPending(message.payload);
        sendResponse({});
      }
      return false;
    };
    chrome.runtime.onMessage.addListener(listener);
    return () => chrome.runtime.onMessage.removeListener(listener);
  }, []);

  const handleDecision = (decision: "approve" | "deny") => {
    if (!pending) return;
    setStatus("Sending...");
    chrome.runtime.sendMessage(
      { type: "SUBMIT_DECISION", request_id: pending.request_id, decision },
      (res) => {
        if (res?.ok) {
          setStatus(`Decision: ${decision}`);
          setPending(null);
          chrome.runtime.sendMessage({ type: "CLEAR_PENDING" });
        } else {
          setStatus(`Error: ${res?.error || "Unknown"}`);
        }
      }
    );
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <p style={styles.text}>Loading...</p>
      </div>
    );
  }

  if (!pending) {
    return (
      <div style={styles.container}>
        <h2 style={styles.title}>Alloist Consent</h2>
        <p style={styles.text}>No pending requests</p>
      </div>
    );
  }

  const actionStr = `${pending.action?.service || ""}.${pending.action?.name || ""}`.replace(/^\./, "") || "unknown";

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Action approval</h2>
      <div style={styles.section}>
        <strong>Agent:</strong> {pending.agent_name}
      </div>
      <div style={styles.section}>
        <strong>Action:</strong> {actionStr}
      </div>
      <div style={styles.section}>
        <strong>Metadata:</strong>
        <pre style={styles.pre}>
          {JSON.stringify(pending.metadata || pending.action?.metadata || {}, null, 2)}
        </pre>
      </div>
      <div style={styles.section}>
        <strong>Risk:</strong>{" "}
        <span
          style={{
            ...styles.badge,
            color:
              pending.risk_level === "high"
                ? "#c00"
                : pending.risk_level === "medium"
                  ? "#c60"
                  : "#060",
          }}
        >
          {pending.risk_level}
        </span>
      </div>
      <div style={styles.buttons}>
        <button
          style={{ ...styles.button, ...styles.approve }}
          onClick={() => handleDecision("approve")}
        >
          Approve
        </button>
        <button
          style={{ ...styles.button, ...styles.deny }}
          onClick={() => handleDecision("deny")}
        >
          Deny
        </button>
      </div>
      {status && <p style={styles.status}>{status}</p>}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: 320,
    padding: 16,
    fontFamily: "system-ui, sans-serif",
    fontSize: 14,
  },
  title: {
    margin: "0 0 12px",
    fontSize: 18,
  },
  text: {
    margin: 0,
    color: "#666",
  },
  section: {
    marginBottom: 10,
  },
  pre: {
    margin: "4px 0 0",
    padding: 8,
    background: "#f5f5f5",
    borderRadius: 4,
    fontSize: 12,
    overflow: "auto",
    maxHeight: 80,
  },
  badge: {
    fontWeight: 600,
  },
  buttons: {
    display: "flex",
    gap: 8,
    marginTop: 16,
  },
  button: {
    flex: 1,
    padding: "10px 16px",
    border: "none",
    borderRadius: 6,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  approve: {
    background: "#0a6",
    color: "white",
  },
  deny: {
    background: "#c00",
    color: "white",
  },
  status: {
    margin: "12px 0 0",
    fontSize: 12,
    color: "#666",
  },
};
