"""Billing routes: checkout placeholder, subscription + usage."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import OrgContext, get_db, require_role
from app.models import OrgRole
from app.services.billing_service import (
    get_limits_for_org,
    get_or_create_subscription,
    get_usage,
)

router = APIRouter(prefix="/billing", tags=["billing"])

ROLE_READ = require_role(OrgRole.admin, OrgRole.developer, OrgRole.viewer)
ROLE_ADMIN = require_role(OrgRole.admin)


@router.post("/checkout", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def create_checkout(
    ctx: OrgContext = ROLE_ADMIN,
) -> dict:
    """Create Stripe checkout session — stub: returns 501."""
    return {
        "message": "Stripe checkout not yet implemented",
        "placeholder_url": "https://checkout.stripe.com/...",
    }


@router.get("/subscription")
def get_subscription(
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> dict:
    """Return current org subscription and usage."""
    sub = get_or_create_subscription(db, ctx.org_id)
    usage = get_usage(db, ctx.org_id)
    limits = get_limits_for_org(db, ctx.org_id)
    return {
        "subscription": {
            "org_id": str(sub.org_id),
            "plan": sub.plan,
            "status": sub.status,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
            "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
        },
        "usage": {
            "period_start": usage.period_start.isoformat(),
            "enforcement_checks": usage.enforcement_checks,
            "tokens_created": usage.tokens_created,
            "policy_evaluations": usage.policy_evaluations,
            "updated_at": usage.updated_at.isoformat() if usage.updated_at else None,
        },
        "limits": limits,
    }
