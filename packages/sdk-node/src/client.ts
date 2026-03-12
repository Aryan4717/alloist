export interface EnforceResponse {
  allowed: boolean;
  reason?: string;
}

export async function postEnforce(
  url: string,
  apiKey: string,
  action: string,
  metadata: Record<string, unknown>
): Promise<EnforceResponse> {
  const base = url.replace(/\/$/, "");
  const res = await fetch(`${base}/enforce`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action, metadata }),
  });

  const data = (await res.json()) as EnforceResponse;

  if (res.status === 403) {
    throw new Error("Action blocked by Alloist policy");
  }
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  if (!data.allowed) {
    throw new Error("Action blocked by Alloist policy");
  }
  return data;
}
