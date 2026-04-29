import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.rbac import require_roles
from app.models.certificate import Certificate
from app.models.job import Job, JobStatus
from app.schemas.certificate import (
    CertificateOut,
    IssueCertificateRequest,
    RenewCertificateRequest,
    RevokeCertificateRequest,
)
from app.services.audit_service import write_audit
from app.services.celery_client import celery_client

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("", response_model=list[CertificateOut])
def list_certificates(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor", "pki-user")), db: Session = Depends(get_db)):
    return db.query(Certificate).order_by(Certificate.id.desc()).limit(200).all()


@router.post("/issue")
def issue_certificate(
    payload: IssueCertificateRequest,
    claims: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-user")),
    db: Session = Depends(get_db),
):
    requested_by = claims.get("preferred_username") or claims.get("sub", "unknown")
    return _enqueue_job(
        db=db,
        task_name="issue_certificate",
        task_path="worker.tasks.certificates.issue_certificate",
        task_kwargs={"common_name": payload.common_name, "sans": payload.sans, "requested_by": requested_by},
        requested_by=requested_by,
        resource=payload.common_name,
        payload=payload.model_dump(),
    )


def _enqueue_job(
    *,
    db: Session,
    task_name: str,
    task_path: str,
    task_kwargs: dict,
    requested_by: str,
    resource: str,
    payload: dict,
):
    task = celery_client.send_task(
        task_path,
        kwargs=task_kwargs,
    )
    job = Job(
        task_name=task_name,
        celery_id=task.id,
        status=JobStatus.pending,
        requested_by=requested_by,
        input_json=json.dumps(payload),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    write_audit(db, actor=requested_by, action=task_name, resource=resource, status="queued")
    return {"job_id": job.id, "celery_id": task.id}


@router.post("/renew")
def renew_certificate(
    payload: RenewCertificateRequest,
    claims: dict = Depends(require_roles("pki-admin", "pki-operator")),
    db: Session = Depends(get_db),
):
    cert = db.query(Certificate).filter(Certificate.id == payload.certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    requested_by = claims.get("preferred_username") or claims.get("sub", "unknown")
    return _enqueue_job(
        db=db,
        task_name="renew_certificate",
        task_path="worker.tasks.certificates.renew_certificate",
        task_kwargs={"certificate_id": cert.id, "requested_by": requested_by},
        requested_by=requested_by,
        resource=cert.common_name,
        payload=payload.model_dump(),
    )


@router.post("/revoke")
def revoke_certificate(
    payload: RevokeCertificateRequest,
    claims: dict = Depends(require_roles("pki-admin", "pki-operator")),
    db: Session = Depends(get_db),
):
    cert = db.query(Certificate).filter(Certificate.id == payload.certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    requested_by = claims.get("preferred_username") or claims.get("sub", "unknown")
    return _enqueue_job(
        db=db,
        task_name="revoke_certificate",
        task_path="worker.tasks.certificates.revoke_certificate",
        task_kwargs={"certificate_id": cert.id, "reason": payload.reason, "requested_by": requested_by},
        requested_by=requested_by,
        resource=cert.common_name,
        payload=payload.model_dump(),
    )
