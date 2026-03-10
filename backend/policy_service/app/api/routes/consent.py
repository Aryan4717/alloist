"""Consent routes: WebSocket for real-time requests, POST /consent/request, POST /consent/decision."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from alloist_logging import get_logger, log_event
from alloist_metrics import create_metrics
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import OrgContext, get_db, require_role
from app.consent_manager import consent_broadcaster
from app.models import OrgRole, PushToken
from app.services.audit_service import log_audit
from app.services.push_service import send_consent_push

router = APIRouter(prefix="/consent", tags=["consent"])
logger = get_logger("policy_service")
metrics = create_metrics("policy_service")

ROLE_READ = require_role(OrgRole.admin, OrgRole.developer, OrgRole.viewer)


class ActionInput(BaseModel):
    service: str = ""
    name: str = ""
    metadata: dict = Field(default_factory=dict)


class ConsentRequestSchema(BaseModel):
    agent_name: str = Field(..., min_length=1)
    token_id: UUID
    action: ActionInput | None = None
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")


class ConsentRequestResponse(BaseModel):
    request_id: str


class ConsentDecisionSchema(BaseModel):
    request_id: str
    decision: str = Field(..., pattern="^(approve|deny)$")


class ConsentDecisionResponse(BaseModel):
    request_id: str
    decision: str


class PendingRequestItem(BaseModel):
    request_id: str
    agent_name: str
    action: dict
    metadata: dict
    risk_level: str
    created_at: str


class PendingListResponse(BaseModel):
    requests: list[PendingRequestItem]


class RegisterDeviceSchema(BaseModel):
    expo_push_token: str = Field(..., min_length=1)
    device_id: str | None = None


class RegisterDeviceResponse(BaseModel):
    ok: bool = True


@router.get("/pending", response_model=PendingListResponse)
def list_pending_requests(ctx: OrgContext = ROLE_READ) -> PendingListResponse:
    """List pending consent requests for the org."""
    items = consent_broadcaster.list_pending(ctx.org_id)
    return PendingListResponse(
        requests=[
            PendingRequestItem(
                request_id=r["request_id"],
                agent_name=r["agent_name"],
                action=r["action"],
                metadata=r["metadata"],
                risk_level=r["risk_level"],
                created_at=r["created_at"],
            )
            for r in items
        ]
    )


@router.post("/register-device", response_model=RegisterDeviceResponse)
def register_device(
    body: RegisterDeviceSchema,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> RegisterDeviceResponse:
    """Register a device for push notifications."""
    existing = (
        db.query(PushToken)
        .filter(
            PushToken.org_id == ctx.org_id,
            PushToken.expo_push_token == body.expo_push_token,
        )
        .first()
    )
    if not existing:
        token = PushToken(
            org_id=ctx.org_id,
            expo_push_token=body.expo_push_token,
            device_id=body.device_id,
        )
        db.add(token)
        db.commit()
    return RegisterDeviceResponse()


@router.websocket("/ws")
async def websocket_consent(websocket: WebSocket) -> None:
    """WebSocket for real-time consent requests. Extension connects here."""
    await consent_broadcaster.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            consent_broadcaster.update_heartbeat(websocket)
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except (json.JSONDecodeError, TypeError):
                pass
    except WebSocketDisconnect:
        consent_broadcaster.disconnect(websocket)


@router.post("/request", response_model=ConsentRequestResponse)
async def create_consent_request(
    body: ConsentRequestSchema,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> ConsentRequestResponse:
    """Create a consent request and broadcast to connected extensions."""
    act = body.action or ActionInput(service="", name="", metadata={})
    action_dict = {"service": act.service, "name": act.name, "metadata": act.metadata}
    request_id, payload = consent_broadcaster.create_consent_request(
        org_id=ctx.org_id,
        token_id=body.token_id,
        agent_name=body.agent_name,
        action=action_dict,
        metadata=act.metadata,
        risk_level=body.risk_level,
    )
    metrics.inc_consent_requests()
    await consent_broadcaster.broadcast_consent_request(payload)
    send_consent_push(db, ctx.org_id, payload)
    return ConsentRequestResponse(request_id=request_id)


@router.post("/decision", response_model=ConsentDecisionResponse)
async def submit_consent_decision(
    body: ConsentDecisionSchema,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> ConsentDecisionResponse:
    """Submit Approve or Deny for a consent request."""
    pending = consent_broadcaster.get_pending(body.request_id)
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent request not found")
    if pending.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Consent already {pending.status}")

    if pending.org_id != ctx.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Request belongs to another org")

    consent_broadcaster.set_decision(body.request_id, body.decision)
    action_str = f"{pending.action.get('service', '')}.{pending.action.get('name', '')}"

    log_event(
        logger,
        action="consent_decision",
        result=body.decision,
        org_id=ctx.org_id,
        user_id=ctx.user_id,
        consent_request_id=body.request_id,
        action_name=action_str,
    )

    log_audit(
        db,
        org_id=ctx.org_id,
        action=action_str,
        result="allow" if body.decision == "approve" else "deny",
        metadata={
            "consent_request_id": body.request_id,
            "agent_name": pending.agent_name,
            "action_metadata": pending.metadata,
            "decision": body.decision,
        },
    )
    return ConsentDecisionResponse(request_id=body.request_id, decision=body.decision)
