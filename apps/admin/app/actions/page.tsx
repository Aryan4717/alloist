"use client";

import { useCallback, useEffect, useState } from "react";
import { listEvidence, type EvidenceItem } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

const POLL_INTERVAL_MS = 5000;

export default function LiveActionsPage() {
  const { jwt, orgId, isConfigured } = useAuth();
  const auth = { jwt, orgId };
  const [items, setItems] = useState<EvidenceItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterResult, setFilterResult] = useState<string>("");
  const [filterAction, setFilterAction] = useState("");

  const fetchEvidence = useCallback(async () => {
    if (!isConfigured) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listEvidence(auth, {
        result: filterResult || undefined,
        action_name: filterAction || undefined,
        limit: 100,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load evidence");
    } finally {
      setLoading(false);
    }
  }, [jwt, orgId, isConfigured, filterResult, filterAction]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  useEffect(() => {
    if (!isConfigured) return;
    const id = setInterval(fetchEvidence, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchEvidence, isConfigured]);

  const formatDate = (s: string) => new Date(s).toLocaleString();

  const tokenSubject = (snap: Record<string, unknown>) => {
    const ts = snap as { scopes?: string[] };
    return Array.isArray(ts.scopes) ? ts.scopes.join(", ") : "—";
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Live Actions
          </h1>
          <p className="text-sm text-muted-foreground">
            Stream of recent enforcement events (evidence). Auto-refreshes every
            5s.
          </p>
        </div>
        <button
          onClick={fetchEvidence}
          disabled={!isConfigured || loading}
          className="rounded-lg border border-border px-4 py-2 font-medium hover:bg-muted disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="mb-6 flex gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Result
          </label>
          <select
            value={filterResult}
            onChange={(e) => setFilterResult(e.target.value)}
            className="rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All</option>
            <option value="allow">Allow</option>
            <option value="deny">Deny</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-foreground">
            Action name
          </label>
          <input
            type="text"
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            placeholder="gmail.send"
            className="rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        {loading && items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            Loading...
          </div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No enforcement events yet. Run a demo agent to see evidence.
          </div>
        ) : (
          <table className="w-full">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Time
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Action
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Result
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Policy ID
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Token scopes
                </th>
              </tr>
            </thead>
            <tbody>
              {items.map((e) => (
                <tr
                  key={e.id}
                  className="border-b border-border last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDate(e.timestamp)}
                  </td>
                  <td className="px-4 py-3 font-medium text-foreground">
                    {e.action_name}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        e.result === "deny"
                          ? "bg-red-100 text-red-800"
                          : "bg-green-100 text-green-800"
                      }`}
                    >
                      {e.result}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {e.policy_id ? `${e.policy_id.slice(0, 8)}...` : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {tokenSubject(e.token_snapshot)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
