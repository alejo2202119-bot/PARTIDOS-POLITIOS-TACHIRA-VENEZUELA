"""Territorial monitoring endpoints (geographic aggregation by state)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core import demo_data

router = APIRouter()


@router.get("/resumen")
async def resumen():
    """Coverage volume + mean sentiment per state (DB view in prod)."""
    return {"items": demo_data.ESTADOS}


@router.get("/estado/{estado_id}")
async def estado(estado_id: str):
    for e in demo_data.ESTADOS:
        if e["id"] == estado_id:
            return e
    raise HTTPException(status_code=404, detail="Estado no encontrado")
