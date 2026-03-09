from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.schemas.evidence import (
    CreateEvidenceRequest,
    CreateEvidenceResponse,
    ExportEvidenceRequest,
    ExportEvidenceResponse,
    EvidenceKeysResponse,
)
from app.services.evidence_service import (
    create_evidence,
    evidence_to_bundle,
    get_evidence,
    get_public_key_b64,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/create", response_model=CreateEvidenceResponse)
def create_evidence_endpoint(
    body: CreateEvidenceRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> CreateEvidenceResponse:
    """Create and store signed evidence record."""
    create_evidence(
        db=db,
        evidence_id=body.evidence_id,
        action_name=body.action_name,
        token_snapshot=body.token_snapshot,
        policy_id=body.policy_id,
        result=body.result,
        runtime_metadata=body.runtime_metadata,
    )
    return CreateEvidenceResponse(evidence_id=body.evidence_id)


@router.post("/export", response_model=ExportEvidenceResponse)
def export_evidence_endpoint(
    body: ExportEvidenceRequest,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> ExportEvidenceResponse:
    """Export signed evidence bundle for auditors."""
    evidence = get_evidence(db, body.evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence not found: {body.evidence_id}",
        )
    public_key = get_public_key_b64()
    bundle = evidence_to_bundle(evidence, public_key)
    return ExportEvidenceResponse(
        bundle=bundle,
        signature=evidence.runtime_signature,
        public_key=public_key,
    )


@router.get("/keys", response_model=EvidenceKeysResponse)
def get_evidence_keys(
    _: None = Depends(verify_api_key),
) -> EvidenceKeysResponse:
    """Get public key for evidence signature verification."""
    return EvidenceKeysResponse(public_key=get_public_key_b64())
