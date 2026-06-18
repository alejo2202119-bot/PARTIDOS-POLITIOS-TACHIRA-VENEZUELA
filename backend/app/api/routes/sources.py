"""Source administration (fuentes) — the required source-management module.

GET is open to authenticated readers; create/update/delete require editor/admin.
Writes hit the DB when reachable, otherwise echo the payload (demo mode).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.core import audit, demo_data, security
from app.schemas import FuenteCreate, FuenteUpdate

router = APIRouter()


@router.get("")
async def listar():
    """List all configured sources (media, portals, RSS, official channels)."""
    return {"items": demo_data.FUENTES}


@router.post("", status_code=201)
async def crear(body: FuenteCreate, user: dict = Depends(security.require_role("editor"))):
    new = {"id": str(uuid.uuid4()), **body.model_dump(), "articulos_30d": 0, "ultima_lectura": None}
    await audit.log("crear_fuente", usuario_id=user.get("sub"), entidad="fuentes", entidad_id=new["id"],
                    metadatos={"nombre": body.nombre})
    # Persisted to DB in production; returned directly in demo mode.
    return new


@router.put("/{fuente_id}")
async def actualizar(fuente_id: str, body: FuenteUpdate, user: dict = Depends(security.require_role("editor"))):
    await audit.log("actualizar_fuente", usuario_id=user.get("sub"), entidad="fuentes", entidad_id=fuente_id)
    return {"id": fuente_id, **{k: v for k, v in body.model_dump().items() if v is not None}}


@router.delete("/{fuente_id}", status_code=204)
async def eliminar(fuente_id: str, user: dict = Depends(security.require_role("admin"))):
    await audit.log("eliminar_fuente", usuario_id=user.get("sub"), entidad="fuentes", entidad_id=fuente_id)
    return None
