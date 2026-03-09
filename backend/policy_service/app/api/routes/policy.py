from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.schemas.policy import (
    CreatePolicyRequest,
    EvaluateRequest,
    EvaluateResponse,
    PolicyResponse,
)
from app.services.evaluator import evaluate
from app.models.policy import Policy

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate_policy(
    body: EvaluateRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> EvaluateResponse:
    """Evaluate whether an action is allowed for a token."""
    result = evaluate(
        token_id=body.token_id,
        action={
            "service": body.action.service,
            "name": body.action.name,
            "metadata": body.action.metadata,
        },
        db=db,
    )
    return EvaluateResponse(
        allowed=result.allowed,
        policy_id=result.policy_id,
        reason=result.reason,
    )


@router.post("", response_model=PolicyResponse)
def create_policy(
    body: CreatePolicyRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Create a new policy."""
    policy = Policy(
        name=body.name,
        description=body.description,
        rules=body.rules,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return PolicyResponse.model_validate(policy)


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> list[PolicyResponse]:
    """List all policies."""
    policies = db.query(Policy).all()
    return [PolicyResponse.model_validate(p) for p in policies]
