from fastapi import Depends, HTTPException, status

from app.core.security import extract_roles, get_current_claims


def require_roles(*required: str):
    def _checker(claims=Depends(get_current_claims)):
        roles = extract_roles(claims)
        if not roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required)}",
            )
        return claims

    return _checker
