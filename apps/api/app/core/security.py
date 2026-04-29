from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

bearer = HTTPBearer(auto_error=True)
_jwks_cache: dict[str, Any] | None = None


def _get_jwks() -> dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is None:
        with httpx.Client(timeout=5.0) as client:
            _jwks_cache = client.get(settings.keycloak_jwks_url).json()
    return _jwks_cache


def _decode_token(token: str) -> dict[str, Any]:
    """
    Keycloak access tokens from the SPA (pki-frontend) usually use aud=account or
    aud=pki-frontend, not pki-api, unless a dedicated audience mapper is configured.
    We verify issuer + signature and skip strict audience so the UI works out of the box.
    """
    jwks = _get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token key")
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def get_current_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> dict[str, Any]:
    return _decode_token(credentials.credentials)


def extract_roles(claims: dict[str, Any]) -> set[str]:
    realm_roles = set(claims.get("realm_access", {}).get("roles", []))
    client_roles = set(claims.get("resource_access", {}).get("pki-api", {}).get("roles", []))
    return realm_roles.union(client_roles)
