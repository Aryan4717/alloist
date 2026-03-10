"""Plan limits for billing. Unlimited = None (no check)."""

PLAN_LIMITS: dict[str, dict[str, int | None]] = {
    "free": {
        "enforcement_checks": 100,
        "tokens_created": 10,
        "policy_evaluations": 100,
    },
    "startup": {
        "enforcement_checks": 10_000,
        "tokens_created": 500,
        "policy_evaluations": 10_000,
    },
    "enterprise": {
        "enforcement_checks": None,
        "tokens_created": None,
        "policy_evaluations": None,
    },
}
