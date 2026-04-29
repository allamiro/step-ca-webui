import json
import os
from datetime import datetime

from sqlalchemy import create_engine, text

from worker.celery_app import celery_app
from worker.services.step_cli_runner import (
    issue_certificate as run_issue_certificate,
    renew_certificate as run_renew_certificate,
    revoke_certificate as run_revoke_certificate,
)
from worker.services.validators import validate_common_name, validate_sans


def _db_engine():
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://pki:pki@postgres:5432/pki")
    return create_engine(database_url, future=True)


def _set_job_status(celery_id: str, status: str, error: str | None = None, output_json: dict | None = None):
    engine = _db_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE jobs SET status=:status, error=:error, output_json=:output_json, updated_at=:updated_at "
                "WHERE celery_id=:celery_id"
            ),
            {
                "status": status,
                "error": error,
                "output_json": json.dumps(output_json) if output_json else None,
                "updated_at": datetime.utcnow(),
                "celery_id": celery_id,
            },
        )


@celery_app.task(name="worker.tasks.certificates.issue_certificate")
def issue_certificate(common_name: str, sans: list[str], requested_by: str):
    engine = _db_engine()
    cn = validate_common_name(common_name)
    valid_sans = validate_sans(sans)

    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE jobs SET status=:status, updated_at=:updated_at "
                "WHERE celery_id=:celery_id"
            ),
            {"status": "running", "updated_at": datetime.utcnow(), "celery_id": issue_certificate.request.id},
        )

    try:
        result = run_issue_certificate(cn, valid_sans)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO certificates (common_name, sans, serial_number, status, issued_by, created_at) "
                    "VALUES (:common_name, :sans, :serial_number, :status, :issued_by, :created_at)"
                ),
                {
                    "common_name": cn,
                    "sans": ",".join(valid_sans),
                    "serial_number": result.get("serial_number"),
                    "status": "active",
                    "issued_by": requested_by,
                    "created_at": datetime.utcnow(),
                },
            )
            conn.execute(
                text(
                    "UPDATE jobs SET status=:status, output_json=:output_json, updated_at=:updated_at "
                    "WHERE celery_id=:celery_id"
                ),
                {
                    "status": "succeeded",
                    "output_json": json.dumps(result),
                    "updated_at": datetime.utcnow(),
                    "celery_id": issue_certificate.request.id,
                },
            )
    except Exception as exc:  # noqa: BLE001
        _set_job_status(issue_certificate.request.id, "failed", error=str(exc))
        raise


@celery_app.task(name="worker.tasks.certificates.renew_certificate")
def renew_certificate(certificate_id: int, requested_by: str):
    engine = _db_engine()
    _set_job_status(renew_certificate.request.id, "running")
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT id, common_name, status FROM certificates WHERE id=:id"),
                {"id": certificate_id},
            ).mappings().first()
            if not row:
                raise ValueError("Certificate not found")
            if row["status"] == "revoked":
                raise ValueError("Cannot renew revoked certificate")
            result = run_renew_certificate(row["common_name"])
            conn.execute(
                text("UPDATE certificates SET status=:status WHERE id=:id"),
                {"status": "active", "id": certificate_id},
            )
            conn.execute(
                text(
                    "INSERT INTO audit_logs (actor, action, resource, status, detail, created_at) "
                    "VALUES (:actor, :action, :resource, :status, :detail, :created_at)"
                ),
                {
                    "actor": requested_by,
                    "action": "renew_certificate",
                    "resource": row["common_name"],
                    "status": "success",
                    "detail": "Renewed via async worker task",
                    "created_at": datetime.utcnow(),
                },
            )
        _set_job_status(
            renew_certificate.request.id,
            "succeeded",
            output_json={"certificate_id": certificate_id, "common_name": row["common_name"], "result": result},
        )
    except Exception as exc:  # noqa: BLE001
        _set_job_status(renew_certificate.request.id, "failed", error=str(exc))
        raise


@celery_app.task(name="worker.tasks.certificates.revoke_certificate")
def revoke_certificate(certificate_id: int, reason: str, requested_by: str):
    engine = _db_engine()
    _set_job_status(revoke_certificate.request.id, "running")
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("SELECT id, common_name FROM certificates WHERE id=:id"),
                {"id": certificate_id},
            ).mappings().first()
            if not row:
                raise ValueError("Certificate not found")
            result = run_revoke_certificate(row["common_name"], reason)
            conn.execute(
                text("UPDATE certificates SET status=:status WHERE id=:id"),
                {"status": "revoked", "id": certificate_id},
            )
            conn.execute(
                text(
                    "INSERT INTO audit_logs (actor, action, resource, status, detail, created_at) "
                    "VALUES (:actor, :action, :resource, :status, :detail, :created_at)"
                ),
                {
                    "actor": requested_by,
                    "action": "revoke_certificate",
                    "resource": row["common_name"],
                    "status": "success",
                    "detail": reason,
                    "created_at": datetime.utcnow(),
                },
            )
        _set_job_status(
            revoke_certificate.request.id,
            "succeeded",
            output_json={
                "certificate_id": certificate_id,
                "reason": reason,
                "common_name": row["common_name"],
                "result": result,
            },
        )
    except Exception as exc:  # noqa: BLE001
        _set_job_status(revoke_certificate.request.id, "failed", error=str(exc))
        raise
