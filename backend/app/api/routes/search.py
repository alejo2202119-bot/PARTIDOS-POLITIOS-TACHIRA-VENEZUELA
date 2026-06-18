"""Intelligent search across actors, narratives, sources and topics."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core import demo_data

router = APIRouter()


@router.get("")
async def buscar(q: str = Query(..., min_length=2)):
    """Unified search returning typed results for the global search box."""
    return {"items": demo_data.buscar(q)}
