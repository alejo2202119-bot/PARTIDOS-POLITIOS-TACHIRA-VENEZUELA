"""Trend analysis + historical comparison endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.core import demo_data

router = APIRouter()
comparativos_router = APIRouter()


@router.get("")
async def tendencias(
    desde: str | None = None,
    hasta: str | None = None,
    tema: str | None = None,
    granularidad: str = "dia",
):
    """Daily mention series per topic (demo dataset)."""
    data = demo_data.TENDENCIAS
    if tema:
        return {"series": [s for s in data["series"] if s["name"] == tema], "emergentes": data["emergentes"]}
    return data


@router.get("/emergentes")
async def emergentes():
    """Emerging topics ranked by recent growth."""
    return demo_data.TENDENCIAS["emergentes"]


# ── Comparativos (mounted under /comparativos) ──────────────────────────────
@comparativos_router.get("")
async def comparativos(desde: str | None = None, hasta: str | None = None, vs: str | None = None):
    """Period-over-period comparison of topic volumes."""
    series = demo_data.TENDENCIAS["series"][:5]
    return {
        "actual": [{"tema": s["name"], "valor": sum(p["y"] for p in s["data"][-7:])} for s in series],
        "anterior": [{"tema": s["name"], "valor": sum(p["y"] for p in s["data"][-14:-7])} for s in series],
    }


@comparativos_router.get("/correlaciones")
async def correlaciones():
    """Correlation strength between topics."""
    return {"items": demo_data.CORRELACIONES}
