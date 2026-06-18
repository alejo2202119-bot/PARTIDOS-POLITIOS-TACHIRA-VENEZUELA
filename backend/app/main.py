"""VPID FastAPI application entrypoint.

Wires CORS, GZip, a request-timing middleware, exception handlers, the
versioned API router and a rich ``/health`` endpoint. External services
(DB / Redis) are probed lazily and never block startup.
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import settings
from app.schemas import HealthOut

logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("vpid")

_START = time.time()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "Plataforma OSINT para el monitoreo y análisis de **información pública** "
        "(medios, RSS, comunicados, APIs autorizadas) sobre actores, partidos, "
        "medios y narrativas políticas. Exportación únicamente en PDF."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Measure and log request duration; expose it via X-Process-Time."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    if elapsed_ms > 1000:
        logger.warning("Slow request %s %s — %.0fms", request.method, request.url.path, elapsed_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})


# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", response_model=HealthOut, tags=["Sistema"])
async def health():
    """Liveness/readiness probe with DB & cache status."""
    from app.core import cache
    from app.database import ping as db_ping

    db_ok = await db_ping()
    cache_ok = await cache.ping()
    return HealthOut(
        status="ok",
        version=settings.VERSION,
        db=db_ok,
        cache=cache_ok,
        demo_mode=settings.DEMO_MODE,
        uptime_s=round(time.time() - _START, 1),
        extra={"env": settings.APP_ENV, "ai_provider": settings.AI_PROVIDER},
    )


@app.get("/", tags=["Sistema"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/api/docs",
        "health": "/health",
        "note": "Procesa exclusivamente información pública. Exportación únicamente en PDF.",
    }


@app.on_event("shutdown")
async def _shutdown():
    from app.database import dispose_engine

    await dispose_engine()
    logger.info("VPID backend shutdown complete")
