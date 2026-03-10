"""Audit log service: log, list, export, and retention cleanup."""

import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog, Organization


def log_audit(
    db: Session,
    org_id: UUID,
    action: str,
    result: str,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Insert an audit log row."""
    log = AuditLog(
        org_id=org_id,
        action=action,
        result=result,
        metadata_=metadata or {},
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_audit_logs(
    db: Session,
    org_id: UUID,
    since: datetime | None = None,
    until: datetime | None = None,
    result: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    """List audit logs with filters. Returns (items, total)."""
    q = db.query(AuditLog).filter(AuditLog.org_id == org_id)
    if since:
        q = q.filter(AuditLog.created_at >= since)
    if until:
        q = q.filter(AuditLog.created_at <= until)
    if result:
        q = q.filter(AuditLog.result == result)
    total = q.count()
    items = q.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()
    return items, total


def delete_expired_logs(db: Session) -> int:
    """Delete logs older than org.retention_days. Returns count deleted."""
    now = datetime.now(timezone.utc)
    orgs = db.query(Organization).all()
    total_deleted = 0
    for org in orgs:
        days = org.retention_days or 30
        cutoff = now - timedelta(days=days)
        deleted = db.query(AuditLog).filter(
            AuditLog.org_id == org.id,
            AuditLog.created_at < cutoff,
        ).delete()
        total_deleted += deleted
    db.commit()
    return total_deleted


def export_audit_logs(
    db: Session,
    org_id: UUID,
    since: datetime | None = None,
    until: datetime | None = None,
    result: str | None = None,
    format: str = "json",
) -> list[dict[str, Any]] | str:
    """
    Export audit logs. Returns list of dicts for JSON, or CSV string for CSV.
    """
    items, _ = list_audit_logs(
        db, org_id, since=since, until=until, result=result, limit=10000, offset=0
    )
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "org_id", "action", "result", "metadata", "created_at"])
        for log in items:
            import json
            meta_str = json.dumps(log.metadata_ or {}) if log.metadata_ else ""
            writer.writerow([
                str(log.id),
                str(log.org_id),
                log.action,
                log.result,
                meta_str,
                log.created_at.isoformat() if log.created_at else "",
            ])
        return buf.getvalue()
    # JSON: return list of dicts
    return [
        {
            "id": str(log.id),
            "org_id": str(log.org_id),
            "action": log.action,
            "result": log.result,
            "metadata": log.metadata_ or {},
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in items
    ]
