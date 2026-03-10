import { getApiKey, getBackendUrl, getOrgId } from "./config";

export interface PendingRequest {
  request_id: string;
  agent_name: string;
  action: { service: string; name: string; metadata?: Record<string, unknown> };
  metadata: Record<string, unknown>;
  risk_level: string;
  created_at: string;
}

export interface PendingListResponse {
  requests: PendingRequest[];
}

export async function fetchPending(): Promise<PendingRequest[]> {
  const base = await getBackendUrl();
  const apiKey = await getApiKey();
  const orgId = await getOrgId();

  const res = await fetch(`${base.replace(/\/$/, "")}/consent/pending`, {
    headers: {
      "X-API-Key": apiKey,
      "X-Org-Id": orgId,
    },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch pending: ${res.status} ${await res.text()}`);
  }

  const data: PendingListResponse = await res.json();
  return data.requests;
}

export async function submitDecision(
  requestId: string,
  decision: "approve" | "deny"
): Promise<void> {
  const base = await getBackendUrl();
  const apiKey = await getApiKey();
  const orgId = await getOrgId();

  const res = await fetch(`${base.replace(/\/$/, "")}/consent/decision`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      "X-Org-Id": orgId,
    },
    body: JSON.stringify({ request_id: requestId, decision }),
  });

  if (!res.ok) {
    throw new Error(`Failed to submit decision: ${res.status} ${await res.text()}`);
  }
}

export async function registerDevice(expoPushToken: string, deviceId?: string): Promise<void> {
  const base = await getBackendUrl();
  const apiKey = await getApiKey();
  const orgId = await getOrgId();

  const res = await fetch(`${base.replace(/\/$/, "")}/consent/register-device`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      "X-Org-Id": orgId,
    },
    body: JSON.stringify({
      expo_push_token: expoPushToken,
      device_id: deviceId ?? undefined,
    }),
  });

  if (!res.ok) {
    throw new Error(`Failed to register device: ${res.status} ${await res.text()}`);
  }
}
