"""Early-warning alert endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core import audit, demo_data, security

router = APIRouter()


@router.get("")
async def listar(estado: str | None = None, severidad: str | None = None):
    items = list(demo_data.ALERTAS)
    if estado:
        items = [a for a in items if a["estado"] == estado]
    if severidad:
        items = [a for a in items if a["severidad"] == severidad]
    return {"items": items}


@router.post("/{alerta_id}/reconocer")
async def reconocer(alerta_id: str, user: dict = Depends(security.require_role("analista"))):
    """Acknowledge an alert (requires analista or higher)."""
    await audit.log("ack_alerta", usuario_id=user.get("sub"), entidad="alertas", entidad_id=alerta_id)
    return {"id": alerta_id, "estado": "reconocida", "ok": True}
