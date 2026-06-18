"""Authentication endpoints (login / refresh / me).

Validates against the DB when reachable; in DEMO_MODE any credentials succeed so
the platform is explorable without a configured user store.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.core import audit, security
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, UserOut

router = APIRouter()


async def _lookup_user(email: str, password: str) -> dict | None:
    """Try to authenticate against the DB; return a user dict or None."""
    try:
        from sqlalchemy import select

        from app.database import get_sessionmaker, ping
        from app.models import Rol, Usuario

        if not await ping():
            return None
        async with get_sessionmaker()() as s:
            row = (await s.execute(select(Usuario, Rol).join(Rol).where(Usuario.email == email))).first()
            if not row:
                return None
            user, rol = row
            if not user.password_hash or not security.verify_password(password, user.password_hash):
                return None
            return {"sub": str(user.id), "email": user.email, "nombre": user.nombre, "rol": rol.nombre}
    except Exception:
        return None


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = await _lookup_user(body.email, body.password)
    if user is None:
        if not settings.DEMO_MODE:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        user = {"sub": body.email, "email": body.email, "nombre": "Administrador (demo)", "rol": "admin"}

    await audit.log("login", usuario_id=user["sub"], entidad="usuarios", metadatos={"email": user["email"]})
    return TokenResponse(
        access_token=security.create_access_token(user["sub"], rol=user["rol"], nombre=user["nombre"], email=user["email"]),
        refresh_token=security.create_refresh_token(user["sub"]),
        user=UserOut(id=user["sub"], email=user.get("email"), nombre=user["nombre"], rol=user["rol"]),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = security.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("not a refresh token")
        sub = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    return TokenResponse(
        access_token=security.create_access_token(sub),
        refresh_token=security.create_refresh_token(sub),
    )


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(security.get_current_user)):
    return UserOut(id=user.get("sub"), email=user.get("email"), nombre=user.get("nombre", "usuario"), rol=user.get("rol", "lector"))
