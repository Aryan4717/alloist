let _apiKey: string | null = null;
let _policyServiceUrl = "http://localhost:8001";

export interface InitOptions {
  apiKey: string;
  policyServiceUrl?: string;
}

export function init(options: InitOptions): void {
  _apiKey = options.apiKey;
  if (options.policyServiceUrl) {
    _policyServiceUrl = options.policyServiceUrl.replace(/\/$/, "");
  }
}

export function getApiKey(): string | null {
  return _apiKey;
}

export function getPolicyServiceUrl(): string {
  return _policyServiceUrl;
}
