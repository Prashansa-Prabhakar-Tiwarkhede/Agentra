"""
Verifies Supabase-issued JWTs. The frontend uses supabase-js for
signup/login/session handling; this backend only ever verifies the
resulting access token — it never handles raw passwords.

Supabase supports two signing setups for user session tokens:
  1. Legacy: HS256, signed with a static shared secret (Settings -> API -> JWT Secret).
  2. Newer: asymmetric signing keys (ES256/RS256), verified via a public JWKS endpoint
     (no shared secret needed) — opt-in per project, most projects are still on (1).

Rather than require guessing which setup a given project uses, this tries the static
secret first (fast, no network call) and falls back to fetching the project's public
JWKS on verification failure. The JWKS is cached in-process since it rarely changes.
"""
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.merchant import Merchant

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

_jwks_cache: dict | None = None


def _fetch_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if not settings.supabase_url:
        return {"keys": []}
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    try:
        resp = httpx.get(url, timeout=5.0)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    except Exception:
        _jwks_cache = {"keys": []}
    return _jwks_cache


def _decode_with_jwks(token: str) -> dict | None:
    jwks = _fetch_jwks()
    if not jwks.get("keys"):
        return None
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        return None
    kid = unverified_header.get("kid")
    matching_key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
    if matching_key is None and len(jwks["keys"]) == 1:
        matching_key = jwks["keys"][0]  # single-key projects don't always set kid
    if matching_key is None:
        return None
    try:
        payload = jwt.decode(
            token, matching_key, algorithms=[matching_key.get("alg", "ES256")], audience="authenticated",
        )
        return payload
    except Exception:
        return None


def get_current_auth_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth token")
    token = credentials.credentials

    payload = None
    # Try legacy static-secret (HS256) verification first — cheapest, no network call.
    if settings.supabase_jwt_secret:
        try:
            payload = jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated",
            )
        except JWTError:
            payload = None

    # Fall back to JWKS-based verification (covers projects on asymmetric signing keys,
    # or cases where the configured static secret is wrong/outdated).
    if payload is None:
        payload = _decode_with_jwks(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    return sub


def get_current_merchant(
    auth_user_id: str = Depends(get_current_auth_user_id),
    db: Session = Depends(get_db),
) -> Merchant:
    merchant = db.query(Merchant).filter(Merchant.auth_user_id == auth_user_id).first()
    if merchant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No merchant profile for this account yet")
    return merchant
