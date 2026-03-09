"use client";

import { useCallback, useEffect, useState } from "react";
import {
  createPolicy,
  deletePolicy,
  listPolicies,
  updatePolicy,
  type Policy,
} from "@/lib/api";
import { useApiKey } from "@/components/ApiKeyProvider";
import { ApiKeyConfig } from "@/components/ApiKeyConfig";
import { POLICY_TEMPLATES, type PolicyTemplate } from "@/lib/templates";

export default function PoliciesPage() {
  const { apiKey, isConfigured } = useApiKey();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Policy | null>(null);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [rulesJson, setRulesJson] = useState("{}");

  const fetchPolicies = useCallback(async () => {
    if (!isConfigured) return;
    setLoading(true);
    setError(null);
    try {
      const list = await listPolicies(apiKey);
      setPolicies(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load policies");
    } finally {
      setLoading(false);
    }
  }, [apiKey, isConfigured]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const openCreate = (template?: PolicyTemplate) => {
    setEditing(null);
    setShowForm(true);
    if (template) {
      setName(template.name);
      setDescription(template.description);
      setRulesJson(JSON.stringify(template.rules, null, 2));
    } else {
      setName("");
      setDescription("");
      setRulesJson("{}");
    }
  };

  const openEdit = (p: Policy) => {
    setEditing(p);
    setShowForm(true);
    setName(p.name);
    setDescription(p.description ?? "");
    setRulesJson(JSON.stringify(p.rules, null, 2));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConfigured) return;
    let rules: Record<string, unknown>;
    try {
      rules = JSON.parse(rulesJson);
    } catch {
      setError("Invalid JSON in rules");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editing) {
        await updatePolicy(apiKey, editing.id, {
          name: name.trim(),
          description: description.trim() || undefined,
          rules,
        });
      } else {
        await createPolicy(apiKey, {
          name: name.trim(),
          description: description.trim() || undefined,
          rules,
        });
      }
      setShowForm(false);
      setEditing(null);
      fetchPolicies();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (p: Policy) => {
    if (!isConfigured || !confirm(`Delete policy "${p.name}"?`)) return;
    try {
      await deletePolicy(apiKey, p.id);
      fetchPolicies();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete");
    }
  };

  const rulesSummary = (r: Record<string, unknown>) => {
    const m = r.match as Record<string, string> | undefined;
    if (m) return `${m.service || "*"}.${m.action_name || "*"}`;
    return "—";
  };

  return (
    <div>
      <ApiKeyConfig />
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Policies
          </h1>
          <p className="text-sm text-muted-foreground">
            Create, edit, and delete policies. Use templates for common flows.
          </p>
        </div>
        <button
          onClick={() => openCreate()}
          disabled={!isConfigured}
          className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
        >
          Create policy
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="mb-8">
        <h2 className="mb-4 font-medium text-foreground">
          Policy templates
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {POLICY_TEMPLATES.map((t) => (
            <div
              key={t.id}
              className="rounded-xl border border-border bg-card p-4 shadow-sm hover:border-primary/50"
            >
              <h3 className="font-medium text-foreground">{t.name}</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                {t.description}
              </p>
              <button
                onClick={() => openCreate(t)}
                disabled={!isConfigured}
                className="mt-3 text-sm font-medium text-primary hover:underline disabled:opacity-50"
              >
                Create from template →
              </button>
            </div>
          ))}
        </div>
      </div>

      {showForm && (
        <div className="mb-6 rounded-xl border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 font-medium text-foreground">
            {editing ? "Edit policy" : "Create policy"}
          </h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Rules (JSON)
              </label>
              <textarea
                value={rulesJson}
                onChange={(e) => setRulesJson(e.target.value)}
                rows={10}
                className="w-full rounded-md border border-border px-3 py-2 font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
              >
                {saving ? "Saving..." : editing ? "Update" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditing(null);
                }}
                className="rounded-lg border border-border px-4 py-2 font-medium hover:bg-muted"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <h2 className="border-b border-border bg-muted/50 px-4 py-3 font-medium text-foreground">
          Existing policies
        </h2>
        {loading ? (
          <div className="p-8 text-center text-muted-foreground">
            Loading...
          </div>
        ) : policies.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            No policies yet. Create one or use a template.
          </div>
        ) : (
          <table className="w-full">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Match
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-foreground">
                  Description
                </th>
                <th className="px-4 py-3 text-right text-sm font-medium text-foreground">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {policies.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-border last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3 font-medium text-foreground">
                    {p.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {rulesSummary(p.rules)}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {p.description || "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEdit(p)}
                      className="mr-3 text-sm font-medium text-primary hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(p)}
                      className="text-sm font-medium text-red-600 hover:text-red-700"
                    >
                      Delete
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
