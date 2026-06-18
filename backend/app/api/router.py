"""Aggregate API router mounting every route module under /api/v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    actors,
    alerts,
    auth,
    dashboard,
    etl,
    narratives,
    news,
    reports,
    search,
    sentiment,
    sources,
    territorial,
    trends,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(news.router, prefix="/articulos", tags=["Noticias"])
api_router.include_router(trends.router, prefix="/tendencias", tags=["Tendencias"])
api_router.include_router(narratives.router, prefix="/narrativas", tags=["Narrativas"])
api_router.include_router(sentiment.router, prefix="/sentimiento", tags=["Sentimiento"])
api_router.include_router(actors.router, prefix="/actores", tags=["Actores"])
api_router.include_router(territorial.router, prefix="/territorial", tags=["Territorial"])
api_router.include_router(alerts.router, prefix="/alertas", tags=["Alertas"])
api_router.include_router(sources.router, prefix="/fuentes", tags=["Fuentes"])
api_router.include_router(reports.router, prefix="/reportes", tags=["Reportes"])
api_router.include_router(search.router, prefix="/buscar", tags=["Búsqueda"])
api_router.include_router(etl.router, prefix="/etl", tags=["ETL"])
# Comparativos shares the trends module's correlation endpoint.
api_router.include_router(trends.comparativos_router, prefix="/comparativos", tags=["Comparativos"])
