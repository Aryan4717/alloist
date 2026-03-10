import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const STORE_KEYS = {
  API_KEY: "api_key",
  ORG_ID: "org_id",
  BACKEND_URL: "backend_url",
} as const;

const DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001";

export function getDefaultBackendUrl(): string {
  if (Platform.OS === "android") {
    return "http://10.0.2.2:8001";
  }
  return "http://localhost:8001";
}

export async function getApiKey(): Promise<string> {
  const v = await SecureStore.getItemAsync(STORE_KEYS.API_KEY);
  return v ?? "dev-api-key";
}

export async function setApiKey(value: string): Promise<void> {
  await SecureStore.setItemAsync(STORE_KEYS.API_KEY, value);
}

export async function getOrgId(): Promise<string> {
  const v = await SecureStore.getItemAsync(STORE_KEYS.ORG_ID);
  return v ?? DEFAULT_ORG_ID;
}

export async function setOrgId(value: string): Promise<void> {
  await SecureStore.setItemAsync(STORE_KEYS.ORG_ID, value);
}

export async function getBackendUrl(): Promise<string> {
  const v = await SecureStore.getItemAsync(STORE_KEYS.BACKEND_URL);
  return v ?? getDefaultBackendUrl();
}

export async function setBackendUrl(value: string): Promise<void> {
  await SecureStore.setItemAsync(STORE_KEYS.BACKEND_URL, value);
}
