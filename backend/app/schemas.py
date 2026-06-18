"""Pydantic v2 request/response models for the API contract.

Analytics endpoints return flexible ``dict`` payloads (computed aggregates),
while auth, pagination and source-CRUD use typed models below.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ─────────────────────────── Generic envelopes ─────────────────────────────
class Page(BaseModel, Generic[T]):
    """Standard paginated list envelope."""

    items: list[T]
    total: int
    page: int = 1
    size: int = 50


# ─────────────────────────── Auth ──────────────────────────────────────────
class LoginRequest(BaseModel):
    # Accepts an email or username identifier (the default admin uses the
    # reserved `.local` domain, which strict EmailStr would reject).
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str | None = None
    email: str | None = None
    nombre: str
    rol: str = "lector"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: UserOut | None = None


# ─────────────────────────── Sources (fuentes) ─────────────────────────────
class FuenteBase(BaseModel):
    nombre: str
    tipo: str = "portal"
    url: str
    rss_url: str | None = None
    alcance: str = "nacional"
    idioma: str = "es"
    pais: str = "VE"
    credibilidad: int = Field(default=50, ge=0, le=100)
    verificada: bool = False
    estado: str = "activa"
    notas: str | None = None


class FuenteCreate(FuenteBase):
    pass


class FuenteUpdate(BaseModel):
    nombre: str | None = None
    tipo: str | None = None
    url: str | None = None
    rss_url: str | None = None
    alcance: str | None = None
    credibilidad: int | None = Field(default=None, ge=0, le=100)
    verificada: bool | None = None
    estado: str | None = None
    notas: str | None = None


class FuenteOut(FuenteBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    articulos_30d: int = 0
    ultima_lectura: datetime | None = None


# ─────────────────────────── Reports ───────────────────────────────────────
class ReporteGenerar(BaseModel):
    tipo: str = "ejecutivo_diario"  # ejecutivo_diario | semanal | ad_hoc
    periodo_desde: date | None = None
    periodo_hasta: date | None = None


class ReporteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    titulo: str
    tipo: str
    estado: str
    periodo_hasta: date | None = None
    archivo_bytes: int | None = None
    created_at: datetime | str | None = None


# ─────────────────────────── Sentiment service ─────────────────────────────
class SentimentResult(BaseModel):
    etiqueta: str
    score: float
    confianza: float
    emociones: dict[str, float] = {}
    modelo: str = "local-lexicon"


# ─────────────────────────── Health ────────────────────────────────────────
class HealthOut(BaseModel):
    status: str
    version: str
    db: bool
    cache: bool
    demo_mode: bool
    uptime_s: float
    extra: dict[str, Any] = {}
