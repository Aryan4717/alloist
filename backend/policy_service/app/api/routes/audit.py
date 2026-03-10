from datetime import datetime

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import OrgContext, get_db, require_role
from app.models import OrgRole
from app.schemas.audit import AuditLogItem, AuditLogListResponse
from app.services.audit_service import export_audit_logs, list_audit_logs

router = APIRouter(prefix="/audit", tags=["audit"])

ROLE_READ = require_role(OrgRole.admin, OrgRole.developer, OrgRole.viewer)


def _parse_datetime(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


@router.get("/logs", response_model=AuditLogListResponse)
def list_audit_logs_endpoint(
    since: str | None = None,
    until: str | None = None,
    result: str | None = None,
    limit: int = 50,
    offset: int = 0,
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """List audit logs with filters. since/until: ISO8601 datetime."""
    since_dt = _parse_datetime(since)
    until_dt = _parse_datetime(until)
    items, total = list_audit_logs(
        db,
        org_id=ctx.org_id,
        since=since_dt,
        until=until_dt,
        result=result,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        logs=[
            AuditLogItem(
                id=log.id,
                org_id=log.org_id,
                action=log.action,
                result=log.result,
                metadata=log.metadata_,
                created_at=log.created_at,
            )
            for log in items
        ],
        total=total,
    )


@router.get("/export")
def export_audit_logs_endpoint(
    since: str | None = None,
    until: str | None = None,
    result: str | None = None,
    format: str = "json",
    ctx: OrgContext = ROLE_READ,
    db: Session = Depends(get_db),
) -> Response:
    """Export audit logs as JSON or CSV."""
    since_dt = _parse_datetime(since)
    until_dt = _parse_datetime(until)
    if format not in ("json", "csv"):
        format = "json"
    data = export_audit_logs(
        db,
        org_id=ctx.org_id,
        since=since_dt,
        until=until_dt,
        result=result,
        format=format,
    )
    if format == "csv":
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
        )
    return JSONResponse(content={"logs": data, "total": len(data)})
