from fastapi import APIRouter, Depends

from app.core.security import extract_roles, get_current_claims

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def me(claims=Depends(get_current_claims)):
    return {
        "sub": claims.get("sub"),
        "preferred_username": claims.get("preferred_username"),
        "email": claims.get("email"),
        "roles": sorted(extract_roles(claims)),
    }
