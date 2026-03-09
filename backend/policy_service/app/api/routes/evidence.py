from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.schemas.evidence import (
    CreateEvidenceRequest,
    CreateEvidenceResponse,
    EvidenceListItem,
    EvidenceListResponse,
    ExportEvidenceRequest,
    ExportEvidenceResponse,
    EvidenceKeysResponse,
)
from app.services.evidence_service import (
    create_evidence,
    evidence_to_bundle,
    get_evidence,
    get_public_key_b64,
    list_evidence,
)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("", response_model=EvidenceListResponse)
def list_evidence_endpoint(
    result: str | None = None,
    action_name: str | None = None,
    since: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    """List evidence with optional filters. since: ISO8601 datetime string."""
    since_dt: datetime | None = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            pass
    items, total = list_evidence(
        db, result=result, action_name=action_name, since=since_dt, limit=limit, offset=offset
    )
    return EvidenceListResponse(
        items=[
            EvidenceListItem(
                id=e.id,
                action_name=e.action_name,
                result=e.result,
                timestamp=e.timestamp,
                policy_id=e.policy_id,
                token_snapshot=e.token_snapshot,
            )
            for e in items
        ],
        total=total,
    )


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
