import { getApiKey, getPolicyServiceUrl } from "./config";
import { postEnforce, EnforceResponse } from "./client";

export async function enforce(
  action: string,
  metadata: Record<string, unknown> = {}
): Promise<EnforceResponse> {
  const apiKey = getApiKey();
  if (!apiKey) {
    throw new Error("Alloist not initialized. Call init({ apiKey }) first.");
  }
  return postEnforce(getPolicyServiceUrl(), apiKey, action, metadata);
}
