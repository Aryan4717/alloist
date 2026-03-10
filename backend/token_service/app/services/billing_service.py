"""Billing service: subscriptions, usage tracking, limit checks."""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.billing.plans import PLAN_LIMITS
from app.models import OrgUsage, Subscription


def _current_period_start() -> date:
    """First day of current billing month."""
    now = datetime.now(timezone.utc)
    return date(now.year, now.month, 1)


def get_or_create_subscription(db: Session, org_id: UUID) -> Subscription:
    """Get or create subscription for org. Default: plan=free, status=active."""
    sub = db.query(Subscription).filter(Subscription.org_id == org_id).first()
    if sub:
        return sub
    sub = Subscription(
        org_id=org_id,
        plan="free",
        status="active",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def get_usage(db: Session, org_id: UUID, period_start: date | None = None) -> OrgUsage:
    """Get or create usage row for org and period."""
    if period_start is None:
        period_start = _current_period_start()
    usage = (
        db.query(OrgUsage)
        .filter(OrgUsage.org_id == org_id, OrgUsage.period_start == period_start)
        .first()
    )
    if usage:
        return usage
    usage = OrgUsage(
        org_id=org_id,
        period_start=period_start,
        enforcement_checks=0,
        tokens_created=0,
        policy_evaluations=0,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def increment_usage(
    db: Session,
    org_id: UUID,
    metric: str,
    amount: int = 1,
) -> None:
    """Increment usage for current month. Metric: enforcement_checks, tokens_created, policy_evaluations."""
    usage = get_usage(db, org_id)
    if metric == "enforcement_checks":
        usage.enforcement_checks += amount
    elif metric == "tokens_created":
        usage.tokens_created += amount
    elif metric == "policy_evaluations":
        usage.policy_evaluations += amount
    else:
        raise ValueError(f"Unknown metric: {metric}")
    usage.updated_at = datetime.now(timezone.utc)
    db.commit()


def get_limits_for_org(db: Session, org_id: UUID) -> dict[str, int | None]:
    """Get usage limits for org based on subscription plan."""
    sub = get_or_create_subscription(db, org_id)
    return PLAN_LIMITS.get(sub.plan, PLAN_LIMITS["free"]).copy()


def check_usage_limit(db: Session, org_id: UUID, metric: str) -> bool:
    """Return True if under limit or unlimited. False if over limit."""
    limits = get_limits_for_org(db, org_id)
    limit = limits.get(metric)
    if limit is None:
        return True
    usage = get_usage(db, org_id)
    if metric == "enforcement_checks":
        current = usage.enforcement_checks
    elif metric == "tokens_created":
        current = usage.tokens_created
    elif metric == "policy_evaluations":
        current = usage.policy_evaluations
    else:
        return True
    return current < limit
