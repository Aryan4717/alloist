export interface PolicyTemplate {
  id: string;
  name: string;
  description: string;
  rules: Record<string, unknown>;
}

export const POLICY_TEMPLATES: PolicyTemplate[] = [
  {
    id: "stripe_high_value_block",
    name: "Block Stripe charges > $1000",
    description: "Deny stripe.charge when metadata.amount exceeds 1000",
    rules: {
      effect: "deny",
      match: { service: "stripe", action_name: "charge" },
      conditions: [
        { field: "metadata.amount", operator: "gt", value: 1000 },
      ],
    },
  },
  {
    id: "gmail_external_send_deny",
    name: "Deny Gmail external sends",
    description: "Deny gmail.send when sending to external recipients",
    rules: {
      effect: "deny",
      match: { service: "gmail", action_name: "send" },
      conditions: [
        { field: "metadata.is_external", operator: "eq", value: true },
      ],
    },
  },
  {
    id: "gmail_send_deny_all",
    name: "Deny all Gmail sends",
    description: "Block all gmail.send (no conditions)",
    rules: {
      effect: "deny",
      match: { service: "gmail", action_name: "send" },
      conditions: [],
    },
  },
  {
    id: "github_merge_block_without_review",
    name: "Block GitHub merge without review",
    description: "Deny github.merge when review_count < 1",
    rules: {
      effect: "deny",
      match: { service: "github", action_name: "merge" },
      conditions: [
        { field: "metadata.review_count", operator: "lt", value: 1 },
      ],
    },
  },
];
