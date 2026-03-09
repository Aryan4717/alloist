"""Placeholder schema for signed evidence bundle of blocked actions."""

# Placeholder: evidence bundle schema for blocked actions
EVIDENCE_BUNDLE_SCHEMA = {
    "type": "object",
    "properties": {
        "evidence_id": {"type": "string", "format": "uuid"},
        "timestamp": {"type": "string", "format": "date-time"},
        "action": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "name": {"type": "string"},
                "metadata": {"type": "object"},
            },
        },
        "result": {"type": "string", "enum": ["blocked"]},
        "reason": {"type": "string"},
        "policy_id": {"type": "string", "format": "uuid"},
        "signature": {"type": "string", "description": "Placeholder for future signature"},
    },
    "required": ["evidence_id", "timestamp", "action", "result", "reason"],
}
