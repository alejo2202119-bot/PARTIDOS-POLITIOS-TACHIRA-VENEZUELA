"""ETL orchestrator — runs the full daily chain and records observability.

ingest → clean → classify → analyze → aggregate. Loads sources/actors from the
DB when reachable, otherwise from the demo dataset, so it can run anywhere.
Each stage is timed and (best-effort) logged to ``etl_ejecuciones``.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from app.core import demo_data
from app.etl import aggregate, analyze, classify, clean, rss_ingest

logger = logging.getLogger("vpid.etl.pipeline")


async def _load_fuentes() -> list[dict]:
    try:
        from sqlalchemy import select

        from app.database import get_sessionmaker, ping
        from app.models import Fuente

        if await ping():
            async with get_sessionmaker()() as s:
                rows = (await s.execute(select(Fuente).where(Fuente.estado == "activa"))).scalars().all()
                if rows:
                    return [{"id": str(f.id), "nombre": f.nombre, "rss_url": f.rss_url,
                             "estado": f.estado, "robots_ok": f.robots_ok} for f in rows]
    except Exception as exc:
        logger.info("Falling back to demo sources: %s", exc)
    return demo_data.FUENTES


async def _record(job: str, estado: str, started: float, items_in=0, items_out=0, items_error=0, log_text="") -> None:
    """Best-effort write to etl_ejecuciones; logs if DB is unavailable."""
    duration_ms = int((time.perf_counter() - started) * 1000)
    try:
        from sqlalchemy import text

        from app.database import get_sessionmaker, ping

        if not await ping():
            raise RuntimeError("db-unreachable")
        async with get_sessionmaker()() as s:
            await s.execute(
                text(
                    "INSERT INTO etl_ejecuciones (job, estado, items_in, items_out, items_error, duracion_ms, log, finalizado_en) "
                    "VALUES (:job, :estado, :i, :o, :e, :d, :log, now())"
                ),
                {"job": job, "estado": estado, "i": items_in, "o": items_out, "e": items_error,
                 "d": duration_ms, "log": log_text[:4000]},
            )
            await s.commit()
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.info("ETL[%s] %s in=%d out=%d err=%d %dms (db skipped: %s)",
                    job, estado, items_in, items_out, items_error, duration_ms, exc)


async def run_full() -> dict:
    """Execute the complete daily pipeline and return a summary."""
    logger.info("=== ETL pipeline start %s ===", datetime.utcnow().isoformat())
    fuentes = await _load_fuentes()
    actores = demo_data.ACTORES  # actor registry; DB-backed in production

    # Stage 1 — ingest
    t = time.perf_counter()
    raw = await rss_ingest.run(fuentes)
    await _record("ingest", "completado", t, items_in=len(fuentes), items_out=len(raw))

    # Stage 2 — clean
    t = time.perf_counter()
    cleaned = clean.run(raw)
    await _record("clean", "completado", t, items_in=len(raw), items_out=len(cleaned))

    # Stage 3 — classify
    t = time.perf_counter()
    classified = classify.run(cleaned)
    await _record("classify", "completado", t, items_in=len(cleaned), items_out=len(classified))

    # Stage 4 — analyze
    t = time.perf_counter()
    analyzed = await analyze.run(classified, actores)
    await _record("analyze", "completado", t, items_in=len(classified), items_out=len(analyzed))

    # Stage 5 — aggregate
    t = time.perf_counter()
    summary = aggregate.run(analyzed)
    await _record("aggregate", "completado", t, items_in=len(analyzed), items_out=1)

    logger.info("=== ETL pipeline done — %d articles, %d alerts ===",
                summary["snapshot"]["total_articulos"], len(summary["alertas"]))
    return summary


async def run_daily_report() -> dict:
    """Generate and store the daily executive PDF (post-pipeline)."""
    from app.services import pdf_report

    meta = pdf_report.generate_and_store()
    logger.info("Daily report generated: %s (%d bytes)", meta["archivo_path"], meta["archivo_bytes"])
    return meta
