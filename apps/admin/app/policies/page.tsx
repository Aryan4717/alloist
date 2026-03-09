"use client";

import { useCallback, useEffect, useState } from "react";
import {
  compilePolicyDsl,
  createPolicy,
  deletePolicy,
  listPolicies,
  updatePolicy,
  type DslRule,
  type Policy,
} from "@/lib/api";
import { useApiKey } from "@/components/ApiKeyProvider";
import { ApiKeyConfig } from "@/components/ApiKeyConfig";
import { POLICY_TEMPLATES, type PolicyTemplate } from "@/lib/templates";

const DEFAULT_DSL = `[
  {
    "id": "example",
    "description": "Example policy",
    "conditions": [
      "action.service == \\"stripe\\"",
      "action.name == \\"charge\\"",
      "metadata.amount > 1000"
    ],
    "effect": "deny"
  }
]`;

export default function PoliciesPage() {
  const { apiKey, isConfigured } = useApiKey();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Policy | null>(null);
  const [saving, setSaving] = useState(false);
  const [editorMode, setEditorMode] = useState<"dsl" | "json">("dsl");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [rulesJson, setRulesJson] = useState("{}");
  const [dslText, setDslText] = useState(DEFAULT_DSL);
  const [validateResult, setValidateResult] = useState<{
    success?: boolean;
    errors?: string[];
    rules?: Record<string, unknown>;
  } | null>(null);
  const [validating, setValidating] = useState(false);

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

  const openCreate = (template?: PolicyTemplate, useDsl?: boolean) => {
    setEditing(null);
    setShowForm(true);
    setValidateResult(null);
    if (template) {
      setName(template.name);
      setDescription(template.description);
      setRulesJson(JSON.stringify(template.rules, null, 2));
      setDslText(template.dsl ?? JSON.stringify([{ id: template.id, description: template.description, conditions: [], effect: "deny" }], null, 2));
      setEditorMode(useDsl ?? !!template.dsl ? "dsl" : "json");
    } else {
      setName("");
      setDescription("");
      setRulesJson("{}");
      setDslText(DEFAULT_DSL);
      setEditorMode("dsl");
    }
  };

  const openEdit = (p: Policy) => {
    setEditing(p);
    setShowForm(true);
    setName(p.name);
    setDescription(p.description ?? "");
    setRulesJson(JSON.stringify(p.rules, null, 2));
    const hasDsl = p.dsl && typeof p.dsl === "object" && "rules" in p.dsl;
    if (hasDsl && Array.isArray((p.dsl as { rules?: unknown }).rules)) {
      setDslText(JSON.stringify((p.dsl as { rules: unknown }).rules, null, 2));
      setEditorMode("dsl");
    } else {
      setDslText(DEFAULT_DSL);
      setEditorMode("json");
    }
    setValidateResult(null);
  };

  const handleValidateDsl = async () => {
    if (!isConfigured) return;
    setValidating(true);
    setValidateResult(null);
    setError(null);
    try {
      const parsed = JSON.parse(dslText) as unknown;
      if (!Array.isArray(parsed) || parsed.length === 0) {
        setValidateResult({ success: false, errors: ["Rules must be a non-empty array"] });
        return;
      }
      const rules: DslRule[] = parsed.map((r: unknown) => {
        const o = r as Record<string, unknown>;
        return {
          id: String(o.id ?? ""),
          description: o.description ? String(o.description) : undefined,
          conditions: Array.isArray(o.conditions) ? o.conditions.map(String) : [],
          effect: (o.effect === "allow" || o.effect === "deny" ? o.effect : "deny") as "allow" | "deny",
        };
      });
      const res = await compilePolicyDsl(apiKey, { rules });
      if (res.errors && res.errors.length > 0) {
        setValidateResult({ success: false, errors: res.errors });
      } else if (res.rules) {
        setValidateResult({ success: true, rules: res.rules });
      }
    } catch (e) {
      setValidateResult({
        success: false,
        errors: [e instanceof Error ? e.message : "Invalid JSON or compile failed"],
      });
    } finally {
      setValidating(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConfigured) return;
    setSaving(true);
    setError(null);

    let rules: Record<string, unknown>;
    let dslPayload: Record<string, unknown> | undefined;

    if (editorMode === "dsl") {
      if (!validateResult?.success || !validateResult.rules) {
        setError("Validate DSL first before saving");
        setSaving(false);
        return;
      }
      rules = validateResult.rules;
      try {
        const parsed = JSON.parse(dslText) as unknown[];
        dslPayload = { rules: parsed };
      } catch {
        dslPayload = undefined;
      }
    } else {
      try {
        rules = JSON.parse(rulesJson) as Record<string, unknown>;
      } catch {
        setError("Invalid JSON in rules");
        setSaving(false);
        return;
      }
    }

    try {
      if (editing) {
        await updatePolicy(apiKey, editing.id, {
          name: name.trim(),
          description: description.trim() || undefined,
          rules,
          dsl: dslPayload,
        });
      } else {
        await createPolicy(apiKey, {
          name: name.trim(),
          description: description.trim() || undefined,
          rules,
          dsl: dslPayload,
        });
      }
      setShowForm(false);
      setEditing(null);
      setValidateResult(null);
      fetchPolicies();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
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
            Create, edit, and delete policies. Use DSL or JSON. Templates for common flows.
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
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => openCreate(t, false)}
                  disabled={!isConfigured}
                  className="text-sm font-medium text-primary hover:underline disabled:opacity-50"
                >
                  Create from template
                </button>
                {t.dsl && (
                  <button
                    onClick={() => openCreate(t, true)}
                    disabled={!isConfigured}
                    className="text-sm font-medium text-muted-foreground hover:text-primary disabled:opacity-50"
                  >
                    Open in DSL
                  </button>
                )}
              </div>
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
              <div className="mb-2 flex items-center gap-4">
                <label className="text-sm font-medium text-foreground">
                  Rules
                </label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditorMode("dsl")}
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      editorMode === "dsl"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    }`}
                  >
                    DSL
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditorMode("json")}
                    className={`rounded px-2 py-1 text-xs font-medium ${
                      editorMode === "json"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground hover:bg-muted/80"
                    }`}
                  >
                    JSON
                  </button>
                </div>
              </div>

              {editorMode === "dsl" ? (
                <div className="space-y-2">
                  <textarea
                    value={dslText}
                    onChange={(e) => {
                      setDslText(e.target.value);
                      setValidateResult(null);
                    }}
                    rows={12}
                    placeholder='[{"id":"...","conditions":["action.service == \"stripe\"",...],"effect":"deny"}]'
                    className="w-full rounded-md border border-border px-3 py-2 font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleValidateDsl}
                      disabled={!isConfigured || validating}
                      className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
                    >
                      {validating ? "Validating..." : "Validate DSL"}
                    </button>
                    {validateResult?.success && (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                        Valid
                      </span>
                    )}
                    {validateResult?.errors && validateResult.errors.length > 0 && (
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                        {validateResult.errors.length} error(s)
                      </span>
                    )}
                  </div>
                  {validateResult?.errors && validateResult.errors.length > 0 && (
                    <ul className="list-inside list-disc text-sm text-red-700">
                      {validateResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <textarea
                  value={rulesJson}
                  onChange={(e) => setRulesJson(e.target.value)}
                  rows={10}
                  className="w-full rounded-md border border-border px-3 py-2 font-mono text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              )}
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={saving || (editorMode === "dsl" && !validateResult?.success)}
                className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground hover:bg-primary-hover disabled:opacity-50"
              >
                {saving ? "Saving..." : editing ? "Update" : "Create"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditing(null);
                  setValidateResult(null);
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
