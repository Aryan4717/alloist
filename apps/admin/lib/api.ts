const TOKEN_URL =
  process.env.NEXT_PUBLIC_TOKEN_SERVICE_URL || "http://localhost:8000";
const POLICY_URL =
  process.env.NEXT_PUBLIC_POLICY_SERVICE_URL || "http://localhost:8001";

function headers(apiKey: string) {
  return {
    "Content-Type": "application/json",
    "X-API-Key": apiKey,
  };
}

export interface TokenMetadata {
  id: string;
  subject: string;
  scopes: string[];
  issued_at: string;
  expires_at: string;
  status: string;
}

export interface TokenListResponse {
  items: TokenMetadata[];
  total: number;
}

export interface Policy {
  id: string;
  name: string;
  description: string | null;
  rules: Record<string, unknown>;
  created_at: string;
}

export interface EvidenceItem {
  id: string;
  action_name: string;
  result: string;
  timestamp: string;
  policy_id: string | null;
  token_snapshot: Record<string, unknown>;
}

export interface EvidenceListResponse {
  items: EvidenceItem[];
  total: number;
}

export interface ExportBundle {
  bundle: Record<string, unknown>;
  signature: string;
  public_key: string;
}

export async function listTokens(
  apiKey: string,
  opts?: { status?: string; subject?: string; limit?: number; offset?: number }
): Promise<TokenListResponse> {
  const params = new URLSearchParams();
  if (opts?.status) params.set("status", opts.status);
  if (opts?.subject) params.set("subject", opts.subject);
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.offset) params.set("offset", String(opts.offset));
  const res = await fetch(`${TOKEN_URL}/tokens?${params}`, {
    headers: headers(apiKey),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createToken(
  apiKey: string,
  body: { subject: string; scopes?: string[]; ttl_seconds?: number }
): Promise<{ token: string; token_id: string; expires_at: string }> {
  const res = await fetch(`${TOKEN_URL}/tokens`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify({
      subject: body.subject,
      scopes: body.scopes ?? [],
      ttl_seconds: body.ttl_seconds ?? 3600,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function revokeToken(
  apiKey: string,
  tokenId: string
): Promise<void> {
  const res = await fetch(`${TOKEN_URL}/tokens/revoke`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify({ token_id: tokenId }),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function listPolicies(apiKey: string): Promise<Policy[]> {
  const res = await fetch(`${POLICY_URL}/policy`, {
    headers: headers(apiKey),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createPolicy(
  apiKey: string,
  body: { name: string; description?: string; rules: Record<string, unknown> }
): Promise<Policy> {
  const res = await fetch(`${POLICY_URL}/policy`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updatePolicy(
  apiKey: string,
  id: string,
  body: { name: string; description?: string; rules: Record<string, unknown> }
): Promise<Policy> {
  const res = await fetch(`${POLICY_URL}/policy/${id}`, {
    method: "PUT",
    headers: headers(apiKey),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deletePolicy(
  apiKey: string,
  id: string
): Promise<void> {
  const res = await fetch(`${POLICY_URL}/policy/${id}`, {
    method: "DELETE",
    headers: headers(apiKey),
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function listEvidence(
  apiKey: string,
  opts?: {
    result?: string;
    action_name?: string;
    since?: string;
    limit?: number;
    offset?: number;
  }
): Promise<EvidenceListResponse> {
  const params = new URLSearchParams();
  if (opts?.result) params.set("result", opts.result);
  if (opts?.action_name) params.set("action_name", opts.action_name);
  if (opts?.since) params.set("since", opts.since);
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.offset) params.set("offset", String(opts.offset));
  const res = await fetch(`${POLICY_URL}/evidence?${params}`, {
    headers: headers(apiKey),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function exportEvidence(
  apiKey: string,
  evidenceId: string
): Promise<ExportBundle> {
  const res = await fetch(`${POLICY_URL}/evidence/export`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify({ evidence_id: evidenceId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
