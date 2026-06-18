"""Executive dashboard endpoints: KPI cards and a compact overview."""

from __future__ import annotations

from fastapi import APIRouter

from app.core import cache, demo_data

router = APIRouter()


async def _kpis_from_db() -> dict | None:
    try:
        from sqlalchemy import select

        from app.database import get_sessionmaker, ping
        from app.models import KpiSnapshot

        if not await ping():
            return None
        async with get_sessionmaker()() as s:
            row = (await s.execute(select(KpiSnapshot).order_by(KpiSnapshot.fecha.desc()).limit(1))).scalar_one_or_none()
            if not row:
                return None
            return {
                "fecha": row.fecha.isoformat(),
                "total_articulos": row.total_articulos,
                "total_menciones": row.total_menciones,
                "fuentes_activas": row.fuentes_activas,
                "sentimiento_global": row.sentimiento_global,
                "narrativas_activas": row.narrativas_activas,
                "narrativas_emergentes": row.narrativas_emergentes,
                "alertas_abiertas": row.alertas_abiertas,
                "alcance_total": row.alcance_total,
                "deltas": demo_data.KPIS["deltas"],
                "spark": demo_data.KPIS["spark"],
            }
    except Exception:
        return None


@router.get("/kpis")
@cache.cached(ttl=120, key="vpid:dashboard:kpis")
async def kpis():
    """KPI cards for the executive dashboard (DB snapshot → demo fallback)."""
    return (await _kpis_from_db()) or demo_data.KPIS


@router.get("/overview")
async def overview():
    """Compact summary: top actors, narratives, recent alerts, sentiment split."""
    return demo_data.overview()
