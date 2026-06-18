"""Narrative detection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core import demo_data

router = APIRouter()


@router.get("")
async def listar(emergente: bool | None = None, tema: str | None = None):
    items = list(demo_data.NARRATIVAS)
    if emergente is not None:
        items = [n for n in items if n["emergente"] == emergente]
    if tema:
        items = [n for n in items if n["tema_id"] == tema]
    return {"items": items}


@router.get("/{narrativa_id}")
async def detalle(narrativa_id: str):
    for n in demo_data.NARRATIVAS:
        if n["id"] == narrativa_id:
            return n
    raise HTTPException(status_code=404, detail="Narrativa no encontrada")
