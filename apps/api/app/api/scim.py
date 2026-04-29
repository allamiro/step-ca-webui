from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.scim import ScimGroup, ScimGroupMember, ScimUser

router = APIRouter(prefix="/scim/v2", tags=["scim"])


def _require_scim_token(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.scim_bearer_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SCIM bearer token")


def _user_resource(user: ScimUser) -> dict:
    return {
        "id": user.id,
        "userName": user.user_name,
        "active": user.active,
        "externalId": user.external_id,
        "name": {"givenName": user.given_name, "familyName": user.family_name},
        "emails": [{"value": user.email, "primary": True}] if user.email else [],
    }


def _group_resource(group: ScimGroup, db: Session) -> dict:
    members = (
        db.query(ScimGroupMember, ScimUser)
        .join(ScimUser, ScimUser.id == ScimGroupMember.user_id)
        .filter(ScimGroupMember.group_id == group.id)
        .all()
    )
    return {
        "id": group.id,
        "displayName": group.display_name,
        "externalId": group.external_id,
        "members": [{"value": user.id, "display": user.user_name} for _, user in members],
    }


@router.get("/Users")
def list_users(
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    users = db.query(ScimUser).order_by(ScimUser.created_at.desc()).all()
    resources = [_user_resource(user) for user in users]
    return {"Resources": resources, "totalResults": len(resources), "startIndex": 1, "itemsPerPage": len(resources)}


@router.post("/Users")
def create_user(
    payload: dict,
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    user_name = payload.get("userName")
    if not user_name:
        raise HTTPException(status_code=400, detail="userName is required")
    if db.query(ScimUser).filter(ScimUser.user_name == user_name).first():
        raise HTTPException(status_code=409, detail="userName already exists")
    emails = payload.get("emails") or []
    first_email = emails[0]["value"] if emails and emails[0].get("value") else None
    name = payload.get("name") or {}
    user = ScimUser(
        user_name=user_name,
        external_id=payload.get("externalId"),
        given_name=name.get("givenName"),
        family_name=name.get("familyName"),
        email=first_email,
        active=payload.get("active", True),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_resource(user)


@router.patch("/Users/{user_id}")
def patch_user(
    user_id: str,
    payload: dict,
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    user = db.query(ScimUser).filter(ScimUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for op in payload.get("Operations", []):
        operation = (op.get("op") or "").lower()
        path = (op.get("path") or "").lower()
        value = op.get("value")
        if operation in {"replace", "add"}:
            if path in {"active"}:
                user.active = bool(value)
            elif path in {"username", "userName".lower()}:
                user.user_name = str(value)
            elif path in {"name.givenname"}:
                user.given_name = str(value)
            elif path in {"name.familyname"}:
                user.family_name = str(value)
            elif path in {"emails"} and isinstance(value, list) and value:
                user.email = value[0].get("value")
            elif isinstance(value, dict):
                if "active" in value:
                    user.active = bool(value["active"])
                if "userName" in value:
                    user.user_name = str(value["userName"])
    db.commit()
    db.refresh(user)
    return _user_resource(user)


@router.get("/Groups")
def list_groups(
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    groups = db.query(ScimGroup).order_by(ScimGroup.created_at.desc()).all()
    resources = [_group_resource(group, db) for group in groups]
    return {"Resources": resources, "totalResults": len(resources), "startIndex": 1, "itemsPerPage": len(resources)}


@router.post("/Groups")
def create_group(
    payload: dict,
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    display_name = payload.get("displayName")
    if not display_name:
        raise HTTPException(status_code=400, detail="displayName is required")
    if db.query(ScimGroup).filter(ScimGroup.display_name == display_name).first():
        raise HTTPException(status_code=409, detail="displayName already exists")
    group = ScimGroup(display_name=display_name, external_id=payload.get("externalId"))
    db.add(group)
    db.commit()
    db.refresh(group)
    members = payload.get("members") or []
    for member in members:
        user_id = member.get("value")
        if user_id and db.query(ScimUser).filter(ScimUser.id == user_id).first():
            db.add(ScimGroupMember(group_id=group.id, user_id=user_id))
    db.commit()
    return _group_resource(group, db)


@router.patch("/Groups/{group_id}")
def patch_group(
    group_id: str,
    payload: dict,
    _: None = Depends(_require_scim_token),
    db: Session = Depends(get_db),
):
    group = db.query(ScimGroup).filter(ScimGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    for op in payload.get("Operations", []):
        operation = (op.get("op") or "").lower()
        path = (op.get("path") or "").lower()
        value = op.get("value")
        if operation in {"replace", "add"} and path in {"displayname", "displayName".lower()}:
            group.display_name = str(value)
        if path.startswith("members") or (not path and isinstance(value, dict) and "members" in value):
            members = value if isinstance(value, list) else value.get("members", []) if isinstance(value, dict) else []
            if operation == "replace":
                db.query(ScimGroupMember).filter(ScimGroupMember.group_id == group.id).delete()
                db.flush()
            if operation in {"add", "replace"}:
                for member in members:
                    user_id = member.get("value")
                    if not user_id:
                        continue
                    exists = (
                        db.query(ScimGroupMember)
                        .filter(ScimGroupMember.group_id == group.id, ScimGroupMember.user_id == user_id)
                        .first()
                    )
                    user = db.query(ScimUser).filter(ScimUser.id == user_id).first()
                    if not exists and user:
                        db.add(ScimGroupMember(group_id=group.id, user_id=user_id))
            if operation == "remove":
                for member in members:
                    user_id = member.get("value")
                    if user_id:
                        db.query(ScimGroupMember).filter(
                            ScimGroupMember.group_id == group.id, ScimGroupMember.user_id == user_id
                        ).delete()
    db.commit()
    db.refresh(group)
    return _group_resource(group, db)
