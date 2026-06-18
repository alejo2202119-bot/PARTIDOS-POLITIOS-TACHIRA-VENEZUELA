"""Public-actor ranking endpoints (based on public-information mentions)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core import demo_data

router = APIRouter()


@router.get("/ranking")
async def ranking(desde: str | None = None, hasta: str | None = None, limit: int = Query(20, ge=1, le=100)):
    """Actors ranked by mention volume (DB view ``v_ranking_actores`` in prod)."""
    return {"items": demo_data.ACTORES[:limit]}


@router.get("")
async def listar():
    return {"items": demo_data.ACTORES}


@router.get("/{actor_id}")
async def detalle(actor_id: str):
    for a in demo_data.ACTORES:
        if a["id"] == actor_id:
            return a
    raise HTTPException(status_code=404, detail="Actor no encontrado")
