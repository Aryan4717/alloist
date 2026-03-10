from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import OrgContext, get_db, require_policy_evaluation_usage, require_role
from app.models import OrgRole, Policy
from app.dsl.compiler import compile_document
from app.services.audit_service import log_audit
from app.schemas.policy import (
    CreatePolicyRequest,
    EvaluateRequest,
    EvaluateResponse,
    PolicyResponse,
)
from app.schemas.policy_dsl import CompileDslRequest, CompileDslResponse
from app.services.evaluator import evaluate

router = APIRouter(prefix="/policy", tags=["policy"])

ROLE_READ = require_role(OrgRole.admin, OrgRole.developer, OrgRole.viewer)
ROLE_WRITE = require_role(OrgRole.admin, OrgRole.developer)
ROLE_ADMIN = require_role(OrgRole.admin)


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_policy(
    body: EvaluateRequest,
    ctx: OrgContext = require_policy_evaluation_usage(OrgRole.admin, OrgRole.developer, OrgRole.viewer),
    db: Session = Depends(get_db),
    x_request_type: str | None = Header(None, alias="X-Request-Type"),
) -> EvaluateResponse:
    """Evaluate whether an action is allowed for a token."""
    result = evaluate(
        org_id=ctx.org_id,
        token_id=body.token_id,
        action={
            "service": body.action.service,
            "name": body.action.name,
            "metadata": body.action.metadata,
        },
        db=db,
    )
    action_str = f"{body.action.service}.{body.action.name}"
    audit_result = "allow" if result.allowed else ("pending" if result.consent_request_id else "deny")
    log_audit(
        db,
        org_id=ctx.org_id,
        action=action_str,
        result=audit_result,
        metadata={
            "token_id": str(body.token_id),
            "policy_id": str(result.policy_id) if result.policy_id else None,
            "reason": result.reason,
            "consent_request_id": result.consent_request_id,
            "action_metadata": body.action.metadata,
        },
    )
    if result.consent_request_id:
        from app.consent_manager import consent_broadcaster
        from app.services.push_service import send_consent_push

        payload = consent_broadcaster.get_broadcast_payload(result.consent_request_id)
        if payload:
            await consent_broadcaster.broadcast_consent_request(payload)
            send_consent_push(db, ctx.org_id, payload)
    from app.services.billing_service import increment_usage

    metric = "enforcement_checks" if x_request_type == "enforcement" else "policy_evaluations"
    increment_usage(db, ctx.org_id, metric)
    return EvaluateResponse(
        allowed=result.allowed,
        policy_id=result.policy_id,
        reason=result.reason,
        consent_request_id=result.consent_request_id,
    )


@router.post("/compile_dsl", response_model=CompileDslResponse)
def compile_dsl(
    body: CompileDslRequest,
    _: OrgContext = ROLE_WRITE,
) -> CompileDslResponse:
    """Compile DSL rules into evaluator rules. Returns compiled rules or errors."""
    try:
        compiled, errors = compile_document(body.rules)
        if errors:
            return CompileDslResponse(rules=None, errors=errors)
        return CompileDslResponse(rules=compiled, errors=None)
    except Exception as e:
        return CompileDslResponse(rules=None, errors=[str(e)])


@router.post("", response_model=PolicyResponse)
def create_policy(
    body: CreatePolicyRequest,
    ctx: OrgContext = ROLE_WRITE,
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Create a new policy."""
    policy = Policy(
        org_id=ctx.org_id,
        name=body.name,
        description=body.description,
        rules=body.rules,
        dsl=body.dsl,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> list[PolicyResponse]:
    """List all policies for org."""
    policies = db.query(Policy).filter(Policy.org_id == ctx.org_id).all()
    return [PolicyResponse.model_validate(p) for p in policies]


@router.put("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: UUID,
    body: CreatePolicyRequest,
    ctx: OrgContext = ROLE_WRITE,
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Update a policy by id."""
    policy = (
        db.query(Policy)
        .filter(Policy.id == policy_id, Policy.org_id == ctx.org_id)
        .first()
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_id}",
        )
    policy.name = body.name
    policy.description = body.description
    policy.rules = body.rules
    policy.dsl = body.dsl
    db.commit()
    db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: UUID,
    ctx: OrgContext = ROLE_ADMIN,
    db: Session = Depends(get_db),
) -> None:
    """Delete a policy by id. Admin only."""
    policy = (
        db.query(Policy)
        .filter(Policy.id == policy_id, Policy.org_id == ctx.org_id)
        .first()
    )
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_id}",
        )
    db.delete(policy)
    db.commit()
