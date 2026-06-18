"""SQLAlchemy 2.0 ORM models mirroring ``database/schema.sql``.

Column names are kept identical to the authoritative schema (Spanish,
snake_case) and enum string values match the PostgreSQL ENUM types exactly.
Enums are declared with ``native_enum=False`` so the models also work against
plain string columns / SQLite in tests without requiring the PG types.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ── Enum value sets (must match schema.sql ENUM definitions) ────────────────
ROL_USUARIO = ("admin", "analista", "editor", "lector")
TIPO_FUENTE = ("medio", "portal", "rss", "blog", "red_social", "comunicado_oficial", "agencia", "otra")
ALCANCE_FUENTE = ("local", "regional", "nacional", "internacional")
ESTADO_FUENTE = ("activa", "pausada", "error", "descartada")
TIPO_ACTOR = ("persona", "organizacion", "partido", "institucion", "medio", "colectivo")
SENTIMIENTO = ("positivo", "neutral", "negativo", "mixto")
NIVEL_RELEVANCIA = ("baja", "media", "alta", "critica")
SEVERIDAD_ALERTA = ("info", "baja", "media", "alta", "critica")
ESTADO_ALERTA = ("abierta", "en_revision", "reconocida", "cerrada")
ESTADO_ARTICULO = ("crudo", "limpio", "clasificado", "analizado", "descartado")
ESTADO_REPORTE = ("generando", "completado", "fallido")
ESTADO_ETL = ("en_cola", "ejecutando", "completado", "fallido", "parcial")


def _uuid_pk() -> Mapped[uuid.UUID]:
    """UUID primary key column with a Python-side default."""
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# ============================================================================
#  Security & administration
# ============================================================================
class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nombre: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    permisos: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    usuarios: Mapped[list[Usuario]] = relationship(back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    rol_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    supabase_uid: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    preferencias: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rol: Mapped[Rol] = relationship(back_populates="usuarios")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    accion: Mapped[str] = mapped_column(Text, nullable=False)
    entidad: Mapped[str | None] = mapped_column(Text)
    entidad_id: Mapped[str | None] = mapped_column(Text)
    metadatos: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    ip: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
#  Geography
# ============================================================================
class Estado(Base):
    __tablename__ = "estados"

    id: Mapped[uuid.UUID] = _uuid_pk()
    codigo: Mapped[str | None] = mapped_column(Text, unique=True)
    nombre: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    capital: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    poblacion: Mapped[int | None] = mapped_column(Integer)

    municipios: Mapped[list[Municipio]] = relationship(back_populates="estado")


class Municipio(Base):
    __tablename__ = "municipios"
    __table_args__ = (UniqueConstraint("estado_id", "nombre"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    estado_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estados.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    capital: Mapped[str | None] = mapped_column(Text)
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)
    poblacion: Mapped[int | None] = mapped_column(Integer)

    estado: Mapped[Estado] = relationship(back_populates="municipios")


# ============================================================================
#  Actors & organizations
# ============================================================================
class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    siglas: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(String(20), default="organizacion", nullable=False)
    tendencia: Mapped[str | None] = mapped_column(Text)
    descripcion: Mapped[str | None] = mapped_column(Text)
    sitio_web: Mapped[str | None] = mapped_column(Text)
    estado_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    actores: Mapped[list[Actor]] = relationship(back_populates="organizacion")


class Actor(Base):
    __tablename__ = "actores"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default="persona", nullable=False)
    cargo: Mapped[str | None] = mapped_column(Text)
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizaciones.id", ondelete="SET NULL")
    )
    estado_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    municipio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("municipios.id"))
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    biografia: Mapped[str | None] = mapped_column(Text)
    foto_url: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organizacion: Mapped[Organizacion | None] = relationship(back_populates="actores")
    menciones: Mapped[list[Mencion]] = relationship(back_populates="actor")


# ============================================================================
#  Sources (REQUIRED administrative table)
# ============================================================================
class Fuente(Base):
    __tablename__ = "fuentes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    rss_url: Mapped[str | None] = mapped_column(Text)
    alcance: Mapped[str] = mapped_column(String(20), default="nacional", nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activa", nullable=False)
    idioma: Mapped[str] = mapped_column(Text, default="es", nullable=False)
    pais: Mapped[str] = mapped_column(Text, default="VE", nullable=False)
    estado_geo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizaciones.id"))
    credibilidad: Mapped[int] = mapped_column(SmallInteger, default=50, nullable=False)
    sesgo: Mapped[str | None] = mapped_column(Text)
    verificada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frecuencia_min: Mapped[int] = mapped_column(Integer, default=360, nullable=False)
    robots_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultima_lectura: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_error: Mapped[str | None] = mapped_column(Text)
    notas: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint("credibilidad BETWEEN 0 AND 100", name="ck_fuentes_credibilidad"),
    )

    articulos: Mapped[list[Articulo]] = relationship(back_populates="fuente")


# ============================================================================
#  Topics
# ============================================================================
class Tema(Base):
    __tablename__ = "temas"

    id: Mapped[uuid.UUID] = _uuid_pk()
    nombre: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    categoria: Mapped[str | None] = mapped_column(Text)
    palabras_clave: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    color: Mapped[str | None] = mapped_column(Text, default="#6366f1")
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
#  Articles + classification & relations
# ============================================================================
class Articulo(Base):
    __tablename__ = "articulos"

    id: Mapped[uuid.UUID] = _uuid_pk()
    fuente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fuentes.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    resumen: Mapped[str | None] = mapped_column(Text)
    contenido: Mapped[str | None] = mapped_column(Text)
    autor: Mapped[str | None] = mapped_column(Text)
    idioma: Mapped[str] = mapped_column(Text, default="es", nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(Text)
    publicado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingerido_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    estado: Mapped[str] = mapped_column(String(20), default="crudo", nullable=False)
    relevancia: Mapped[str] = mapped_column(String(20), default="media", nullable=False)
    alcance_estimado: Mapped[int | None] = mapped_column(Integer)
    estado_geo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    municipio_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("municipios.id"))
    tema_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("temas.id"))
    metadatos: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    fuente: Mapped[Fuente] = relationship(back_populates="articulos")
    menciones: Mapped[list[Mencion]] = relationship(back_populates="articulo")
    analisis: Mapped[list[AnalisisSentimiento]] = relationship(back_populates="articulo")


class Mencion(Base):
    __tablename__ = "menciones"
    __table_args__ = (
        CheckConstraint(
            "actor_id IS NOT NULL OR organizacion_id IS NOT NULL",
            name="ck_menciones_actor_or_org",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    articulo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articulos.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("actores.id", ondelete="CASCADE")
    )
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizaciones.id", ondelete="CASCADE")
    )
    fragmento: Mapped[str | None] = mapped_column(Text)
    peso: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articulo: Mapped[Articulo] = relationship(back_populates="menciones")
    actor: Mapped[Actor | None] = relationship(back_populates="menciones")


class AnalisisSentimiento(Base):
    __tablename__ = "analisis_sentimiento"
    __table_args__ = (
        CheckConstraint("score BETWEEN -1 AND 1", name="ck_sent_score"),
        CheckConstraint("confianza BETWEEN 0 AND 1", name="ck_sent_confianza"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    articulo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articulos.id", ondelete="CASCADE"), nullable=False
    )
    mencion_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("menciones.id", ondelete="CASCADE")
    )
    etiqueta: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confianza: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    emociones: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    modelo: Mapped[str] = mapped_column(Text, default="local-lexicon", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articulo: Mapped[Articulo] = relationship(back_populates="analisis")


# ============================================================================
#  Narratives
# ============================================================================
class Narrativa(Base):
    __tablename__ = "narrativas"

    id: Mapped[uuid.UUID] = _uuid_pk()
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    palabras_clave: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    tema_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("temas.id"))
    sentimiento: Mapped[str | None] = mapped_column(String(20))
    relevancia: Mapped[str] = mapped_column(String(20), default="media", nullable=False)
    emergente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primera_vista: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultima_vista: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_articulos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alcance_estimado: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    articulos: Mapped[list[NarrativaArticulo]] = relationship(back_populates="narrativa")


class NarrativaArticulo(Base):
    __tablename__ = "narrativa_articulos"

    narrativa_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("narrativas.id", ondelete="CASCADE"), primary_key=True
    )
    articulo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("articulos.id", ondelete="CASCADE"), primary_key=True
    )
    similitud: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    narrativa: Mapped[Narrativa] = relationship(back_populates="articulos")


# ============================================================================
#  Trends + KPI snapshots
# ============================================================================
class Tendencia(Base):
    __tablename__ = "tendencias"
    __table_args__ = (
        UniqueConstraint(
            "fecha", "tema_id", "actor_id", "organizacion_id", "estado_geo_id"
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tema_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("temas.id"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("actores.id"))
    organizacion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizaciones.id"))
    estado_geo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    menciones: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alcance_estimado: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sentimiento_prom: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    variacion_pct: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id: Mapped[uuid.UUID] = _uuid_pk()
    fecha: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    total_articulos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_menciones: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fuentes_activas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentimiento_global: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    narrativas_activas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    narrativas_emergentes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alertas_abiertas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    alcance_total: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    detalle: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
#  Alerts
# ============================================================================
class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[uuid.UUID] = _uuid_pk()
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), default="media", nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="abierta", nullable=False)
    tema_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("temas.id"))
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("actores.id"))
    estado_geo_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("estados.id"))
    narrativa_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("narrativas.id"))
    umbral: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    valor: Mapped[float | None] = mapped_column(Float)
    asignada_a: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    reconocida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ============================================================================
#  Reports (PDF only)
# ============================================================================
class Reporte(Base):
    __tablename__ = "reportes"

    id: Mapped[uuid.UUID] = _uuid_pk()
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, default="ejecutivo_diario", nullable=False)
    periodo_desde: Mapped[date | None] = mapped_column(Date)
    periodo_hasta: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), default="generando", nullable=False)
    archivo_path: Mapped[str | None] = mapped_column(Text)
    archivo_bytes: Mapped[int | None] = mapped_column(BigInteger)
    pdf_sha256: Mapped[str | None] = mapped_column(Text)
    resumen: Mapped[str | None] = mapped_column(Text)
    parametros: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    generado_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ============================================================================
#  ETL orchestration / observability
# ============================================================================
class EtlEjecucion(Base):
    __tablename__ = "etl_ejecuciones"

    id: Mapped[uuid.UUID] = _uuid_pk()
    job: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="en_cola", nullable=False)
    fuente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fuentes.id", ondelete="SET NULL")
    )
    items_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_error: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duracion_ms: Mapped[int | None] = mapped_column(Integer)
    log: Mapped[str | None] = mapped_column(Text)
    iniciado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
