export interface ConsentRequest {
  type: "consent_request";
  request_id: string;
  agent_name: string;
  action: { service: string; name: string; metadata?: Record<string, unknown> };
  metadata?: Record<string, unknown>;
  risk_level: string;
}
