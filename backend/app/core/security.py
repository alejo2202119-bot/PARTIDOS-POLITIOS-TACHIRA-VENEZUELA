"""Authentication & authorization: password hashing, JWT, RBAC dependencies.

In ``DEMO_MODE`` (non-production) a missing/relaxed setup still works: any
credentials log in and the current user defaults to an ``admin`` so the API is
fully explorable. In production, real JWTs and role checks are enforced.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ROLE_ORDER = {"lector": 0, "editor": 1, "analista": 2, "admin": 3}


# ─────────────────────────── Passwords ─────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ─────────────────────────── JWT ───────────────────────────────────────────
def _create_token(data: dict[str, Any], expires: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(sub: str, rol: str = "lector", **extra: Any) -> str:
    return _create_token(
        {"sub": sub, "rol": rol, "type": "access", **extra},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(sub: str) -> str:
    return _create_token(
        {"sub": sub, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ─────────────────────────── Dependencies ──────────────────────────────────
async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict[str, Any]:
    """Resolve the current user from the bearer token.

    Falls back to a demo admin in non-production so the API stays explorable.
    """
    if not token:
        if settings.DEMO_MODE:
            return {"sub": "demo", "nombre": "Administrador (demo)", "rol": "admin", "email": "admin@vpid.local"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")

    try:
        payload = decode_token(token)
        return {
            "sub": payload.get("sub"),
            "rol": payload.get("rol", "lector"),
            "nombre": payload.get("nombre", payload.get("sub", "usuario")),
            "email": payload.get("email"),
        }
    except JWTError:
        if settings.DEMO_MODE:
            return {"sub": "demo", "nombre": "Administrador (demo)", "rol": "admin"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


def require_role(*roles: str):
    """Dependency factory enforcing a minimum role (RBAC, hierarchical)."""

    min_rank = min(ROLE_ORDER.get(r, 0) for r in roles) if roles else 0

    async def _dep(user: dict = Depends(get_current_user)) -> dict:
        if settings.DEMO_MODE:
            return user
        if ROLE_ORDER.get(user.get("rol", "lector"), 0) < min_rank:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return user

    return _dep
