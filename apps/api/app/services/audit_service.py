from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(db: Session, actor: str, action: str, resource: str, status: str, detail: str | None = None) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            resource=resource,
            status=status,
            detail=detail,
        )
    )
    db.commit()
