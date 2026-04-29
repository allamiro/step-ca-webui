import json

from celery.exceptions import TimeoutError as CeleryTimeoutError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.rbac import require_roles
from app.core.security import extract_roles, get_current_claims
from app.models.audit_log import AuditLog
from app.models.setting import Setting
from app.services.celery_client import celery_client

router = APIRouter(tags=["misc"])


@router.get("/audit-logs")
def get_audit_logs(_: dict = Depends(require_roles("pki-admin", "pki-auditor")), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()
    return [
        {
            "id": row.id,
            "actor": row.actor,
            "action": row.action,
            "resource": row.resource,
            "status": row.status,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/provisioners")
def list_provisioners(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor"))):
    async_result = celery_client.send_task("worker.tasks.provisioners.list_provisioners")
    try:
        return async_result.get(timeout=60)
    except CeleryTimeoutError as exc:
        raise HTTPException(status_code=504, detail="Provisioner list task timed out") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/acme")
def acme_info(_: dict = Depends(require_roles("pki-admin", "pki-operator", "pki-auditor"))):
    base = settings.step_ca_url.rstrip("/")
    return {
        "enabled": True,
        "directory_url": f"{base}/acme/acme/directory",
        "new_nonce_url": f"{base}/acme/acme/new-nonce",
        "new_account_url": f"{base}/acme/acme/new-account",
        "new_order_url": f"{base}/acme/acme/new-order",
        "note": "These URLs are served by step-ca when ACME is enabled in ca.json.",
    }


@router.get("/users")
def users(claims: dict = Depends(require_roles("pki-admin"))):
    username = claims.get("preferred_username") or claims.get("sub", "unknown")
    roles = sorted(extract_roles(claims))
    return {
        "items": [
            {
                "username": username,
                "email": claims.get("email"),
                "roles": roles,
                "source": "keycloak-jwt",
            }
        ]
    }


@router.get("/settings")
def get_settings(_: dict = Depends(require_roles("pki-admin")), db: Session = Depends(get_db)):
    default_value = {
        "security": {
            "require_approval": False,
            "allow_wildcard_certificates": False,
            "max_sans_per_request": 20,
        }
    }
    row = db.query(Setting).filter(Setting.key == "platform").first()
    if not row:
        row = Setting(key="platform", value_json=json.dumps(default_value), updated_by="system")
        db.add(row)
        db.commit()
        db.refresh(row)
    return json.loads(row.value_json)


@router.put("/settings")
def set_settings(payload: dict, claims: dict = Depends(require_roles("pki-admin")), db: Session = Depends(get_db)):
    username = claims.get("preferred_username") or claims.get("sub", "unknown")
    row = db.query(Setting).filter(Setting.key == "platform").first()
    if not row:
        row = Setting(key="platform", value_json=json.dumps(payload), updated_by=username)
        db.add(row)
    else:
        row.value_json = json.dumps(payload)
        row.updated_by = username
    db.commit()
    return {"ok": True, "updated_by": username, "settings": payload}


@router.get("/whoami")
def whoami(claims: dict = Depends(get_current_claims)):
    return {
        "username": claims.get("preferred_username"),
        "email": claims.get("email"),
        "roles": sorted(extract_roles(claims)),
    }
