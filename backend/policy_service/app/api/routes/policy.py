from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.dsl.compiler import compile_document
from app.schemas.policy import (
    CreatePolicyRequest,
    EvaluateRequest,
    EvaluateResponse,
    PolicyResponse,
)
from app.schemas.policy_dsl import CompileDslRequest, CompileDslResponse
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


@router.post("/compile_dsl", response_model=CompileDslResponse)
def compile_dsl(
    body: CompileDslRequest,
    _: None = Depends(verify_api_key),
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
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Create a new policy."""
    policy = Policy(
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
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> list[PolicyResponse]:
    """List all policies."""
    policies = db.query(Policy).all()
    return [PolicyResponse.model_validate(p) for p in policies]


@router.put("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: UUID,
    body: CreatePolicyRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Update a policy by id."""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
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
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> None:
    """Delete a policy by id."""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy not found: {policy_id}",
        )
    db.delete(policy)
    db.commit()
