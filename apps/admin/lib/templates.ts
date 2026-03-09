export interface PolicyTemplate {
  id: string;
  name: string;
  description: string;
  rules: Record<string, unknown>;
  dsl?: string; // DSL snippet for editor (JSON string of rules array)
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
    dsl: `[
  {
    "id": "stripe_high_value",
    "description": "Block charges > 1000",
    "conditions": [
      "action.service == \\"stripe\\"",
      "action.name == \\"charge\\"",
      "metadata.amount > 1000"
    ],
    "effect": "deny"
  }
]`,
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
    dsl: `[
  {
    "id": "gmail_external",
    "description": "Deny external sends",
    "conditions": [
      "action.service == \\"gmail\\"",
      "action.name == \\"send\\"",
      "metadata.is_external == true"
    ],
    "effect": "deny"
  }
]`,
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
    dsl: `[
  {
    "id": "gmail_deny_all",
    "description": "Block all gmail.send",
    "conditions": [
      "action.service == \\"gmail\\"",
      "action.name == \\"send\\""
    ],
    "effect": "deny"
  }
]`,
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
    dsl: `[
  {
    "id": "github_merge_no_review",
    "description": "Block merge without review",
    "conditions": [
      "action.service == \\"github\\"",
      "action.name == \\"merge\\"",
      "metadata.review_count < 1"
    ],
    "effect": "deny"
  }
]`,
  },
];
