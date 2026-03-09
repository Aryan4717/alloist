"use client";

import { useCallback, useEffect, useState } from "react";
import { exportEvidence, listEvidence, type EvidenceItem } from "@/lib/api";
import { useApiKey } from "@/components/ApiKeyProvider";
import { ApiKeyConfig } from "@/components/ApiKeyConfig";

export default function ExportsPage() {
  const { apiKey, isConfigured } = useApiKey();
  const [items, setItems] = useState<EvidenceItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  const fetchEvidence = useCallback(async () => {
    if (!isConfigured) return;
    setLoading(true);
    setError(null);
    try {
      const res = await listEvidence(apiKey, { limit: 100 });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load evidence");
    } finally {
      setLoading(false);
    }
  }, [apiKey, isConfigured]);

  useEffect(() => {
    fetchEvidence();
  }, [fetchEvidence]);

  const handleExport = async (e: EvidenceItem) => {
    if (!isConfigured) return;
    setExporting(e.id);
    try {
      const data = await exportEvidence(apiKey, e.id);
      const blob = new Blob(
        [
          JSON.stringify(
            {
              bundle: data.bundle,
              signature: data.signature,
              public_key: data.public_key,
            },
            null,
            2
          ),
        ],
        { type: "application/json" }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `evidence_${e.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(null);
    }
  };

  const formatDate = (s: string) => new Date(s).toLocaleString();

  return (
    <div>
      <ApiKeyConfig />
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Evidence Exports
        </h1>
        <p className="text-sm text-muted-foreground">
          Download signed evidence bundles for audit and verification.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">
            Loading...
          </div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No evidence yet. Run a demo agent that gets blocked to create
            evidence.
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
                <th className="px-4 py-3 text-right text-sm font-medium text-foreground">
                  Export
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
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleExport(e)}
                      disabled={exporting === e.id || !isConfigured}
                      className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
                    >
                      {exporting === e.id ? "..." : "Export"}
                    </button>
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
