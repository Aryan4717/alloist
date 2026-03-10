"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createToken,
  listTokens,
  revokeToken,
  type TokenMetadata,
} from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export default function TokensPage() {
  const { jwt, orgId, isConfigured } = useAuth();
  const auth = { jwt, orgId };
  const [tokens, setTokens] = useState<TokenMetadata[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [subject, setSubject] = useState("");
  const [scopes, setScopes] = useState("");
  const [ttl, setTtl] = useState(3600);

  const fetchTokens = useCallback(async () => {
    if (!isConfigured) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listTokens(auth, { limit: 100 });
      setTokens(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tokens");
    } finally {
      setLoading(false);
    }
  }, [jwt, orgId, isConfigured]);

  useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConfigured) return;
    setCreating(true);
    setError(null);
    try {
      await createToken(auth, {
        subject: subject.trim(),
        scopes: scopes ? scopes.split(",").map((s) => s.trim()) : [],
        ttl_seconds: ttl,
      });
      setShowCreate(false);
      setSubject("");
      setScopes("");
      setTtl(3600);
      fetchTokens();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create token");
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (id: string) => {
    if (!isConfigured || !confirm("Revoke this token?")) return;
    try {
      await revokeToken(auth, id);
      fetchTokens();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to revoke");
    }
  };

  const formatDate = (s: string) =>
    new Date(s).toLocaleString();

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Tokens
          </h1>
          <p className="text-sm text-muted-foreground">
            Create and revoke capability tokens for agents.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          disabled={!isConfigured}
          className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
        >
          Create token
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {showCreate && (
        <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 font-medium text-foreground">Create token</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Subject
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
                placeholder="agent-1"
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Scopes (comma-separated)
              </label>
              <input
                type="text"
                value={scopes}
                onChange={(e) => setScopes(e.target.value)}
                placeholder="read, email:send"
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                TTL (seconds)
              </label>
              <input
                type="number"
                value={ttl}
                onChange={(e) => setTtl(Number(e.target.value))}
                min={60}
                max={31536000}
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating}
                className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
              >
                {creating ? "Creating..." : "Create"}
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-lg border border-border px-4 py-2 font-medium hover:bg-muted"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">
            Loading...
          </div>
        ) : tokens.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No tokens yet. Create one to get started.
          </div>
        ) : (
          <table className="w-full">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Subject
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Scopes
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Expires
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {tokens.map((t) => (
                <tr
                  key={t.id}
                  className="border-b border-border last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {t.id.slice(0, 8)}...
                  </td>
                  <td className="px-4 py-3 text-sm text-foreground">
                    {t.subject}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {t.scopes?.length ? t.scopes.join(", ") : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        t.status === "active"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {t.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDate(t.expires_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {t.status === "active" && (
                      <button
                        onClick={() => handleRevoke(t.id)}
                        className="text-sm font-medium text-red-600 hover:text-red-700"
                      >
                        Revoke
                      </button>
                    )}
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
