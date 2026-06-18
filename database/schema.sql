-- ============================================================================
--  Venezuela Political Intelligence Dashboard (VPID)
--  PostgreSQL 15+ / Supabase-compatible schema
--
--  Scope: analysis of PUBLIC, openly available information only
--  (published media, RSS, official communiqués, authorized public APIs).
--
--  Conventions:
--    * Primary keys: uuid (gen_random_uuid)
--    * Timestamps: timestamptz, stored in UTC
--    * Soft-deletes via `deleted_at` where relevant
--    * snake_case identifiers, Spanish domain names
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- fuzzy text search / similarity
CREATE EXTENSION IF NOT EXISTS "unaccent";    -- accent-insensitive search
CREATE EXTENSION IF NOT EXISTS "citext";      -- case-insensitive email column
                                              -- (must exist before usuarios.email below)

-- ----------------------------------------------------------------------------
--  ENUM TYPES
-- ----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE rol_usuario       AS ENUM ('admin', 'analista', 'editor', 'lector');
    CREATE TYPE tipo_fuente       AS ENUM ('medio', 'portal', 'rss', 'blog', 'red_social', 'comunicado_oficial', 'agencia', 'otra');
    CREATE TYPE alcance_fuente    AS ENUM ('local', 'regional', 'nacional', 'internacional');
    CREATE TYPE estado_fuente     AS ENUM ('activa', 'pausada', 'error', 'descartada');
    CREATE TYPE tipo_actor        AS ENUM ('persona', 'organizacion', 'partido', 'institucion', 'medio', 'colectivo');
    CREATE TYPE sentimiento       AS ENUM ('positivo', 'neutral', 'negativo', 'mixto');
    CREATE TYPE nivel_relevancia  AS ENUM ('baja', 'media', 'alta', 'critica');
    CREATE TYPE severidad_alerta  AS ENUM ('info', 'baja', 'media', 'alta', 'critica');
    CREATE TYPE estado_alerta     AS ENUM ('abierta', 'en_revision', 'reconocida', 'cerrada');
    CREATE TYPE estado_articulo   AS ENUM ('crudo', 'limpio', 'clasificado', 'analizado', 'descartado');
    CREATE TYPE estado_reporte    AS ENUM ('generando', 'completado', 'fallido');
    CREATE TYPE estado_etl        AS ENUM ('en_cola', 'ejecutando', 'completado', 'fallido', 'parcial');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ----------------------------------------------------------------------------
--  updated_at trigger helper
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- ============================================================================
--  SECURITY & ADMINISTRATION
-- ============================================================================

CREATE TABLE roles (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre       rol_usuario NOT NULL UNIQUE,
    descripcion  text,
    permisos     jsonb NOT NULL DEFAULT '{}'::jsonb,   -- granular permission map
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE usuarios (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           citext UNIQUE,                      -- requires citext; fallback below
    nombre          text NOT NULL,
    rol_id          uuid NOT NULL REFERENCES roles(id),
    password_hash   text,                               -- null when delegated to Supabase Auth
    supabase_uid    uuid,                               -- link to auth.users when used
    activo          boolean NOT NULL DEFAULT true,
    ultimo_acceso   timestamptz,
    preferencias    jsonb NOT NULL DEFAULT '{"tema":"oscuro","locale":"es"}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_usuarios_updated BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Append-only audit trail (who did what, when, from where)
CREATE TABLE auditoria (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id   uuid REFERENCES usuarios(id) ON DELETE SET NULL,
    accion       text NOT NULL,            -- e.g. 'login', 'export_pdf', 'update_fuente'
    entidad      text,                     -- table / module affected
    entidad_id   text,
    metadatos    jsonb NOT NULL DEFAULT '{}'::jsonb,
    ip           inet,
    user_agent   text,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_auditoria_usuario ON auditoria(usuario_id);
CREATE INDEX idx_auditoria_created ON auditoria(created_at DESC);

-- ============================================================================
--  GEOGRAPHY (Venezuela)
-- ============================================================================

CREATE TABLE estados (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo       text UNIQUE,             -- ISO 3166-2:VE e.g. 'VE-S' (Táchira)
    nombre       text NOT NULL UNIQUE,
    capital      text,
    region       text,                    -- e.g. 'Los Andes'
    latitud      double precision,
    longitud     double precision,
    poblacion    integer
);

CREATE TABLE municipios (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    estado_id    uuid NOT NULL REFERENCES estados(id) ON DELETE CASCADE,
    nombre       text NOT NULL,
    capital      text,
    latitud      double precision,
    longitud     double precision,
    poblacion    integer,
    UNIQUE (estado_id, nombre)
);
CREATE INDEX idx_municipios_estado ON municipios(estado_id);

-- ============================================================================
--  ACTORS & ORGANIZATIONS (public political figures / parties / media)
-- ============================================================================

CREATE TABLE organizaciones (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre       text NOT NULL,
    siglas       text,
    tipo         tipo_actor NOT NULL DEFAULT 'organizacion',
    tendencia    text,                    -- e.g. 'oposicion', 'oficialismo', 'independiente'
    descripcion  text,
    sitio_web    text,
    estado_id    uuid REFERENCES estados(id),
    activo       boolean NOT NULL DEFAULT true,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_org_updated BEFORE UPDATE ON organizaciones
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE INDEX idx_org_nombre_trgm ON organizaciones USING gin (nombre gin_trgm_ops);

CREATE TABLE actores (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          text NOT NULL,
    tipo            tipo_actor NOT NULL DEFAULT 'persona',
    cargo           text,                 -- public role, e.g. 'Gobernador', 'Diputado'
    organizacion_id uuid REFERENCES organizaciones(id) ON DELETE SET NULL,
    estado_id       uuid REFERENCES estados(id),
    municipio_id    uuid REFERENCES municipios(id),
    aliases         text[] NOT NULL DEFAULT '{}',   -- alternative public names for matching
    biografia       text,                 -- public bio summary
    foto_url        text,
    activo          boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_actores_updated BEFORE UPDATE ON actores
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE INDEX idx_actores_org ON actores(organizacion_id);
CREATE INDEX idx_actores_nombre_trgm ON actores USING gin (nombre gin_trgm_ops);

-- ============================================================================
--  FUENTES — open, verifiable sources (media, portals, RSS, official channels)
--  (REQUIRED administrative table for managing where information comes from)
-- ============================================================================

CREATE TABLE fuentes (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre           text NOT NULL,
    tipo             tipo_fuente NOT NULL,
    url              text NOT NULL,
    rss_url          text,                          -- feed URL when applicable
    alcance          alcance_fuente NOT NULL DEFAULT 'nacional',
    estado           estado_fuente NOT NULL DEFAULT 'activa',
    idioma           text NOT NULL DEFAULT 'es',
    pais             text NOT NULL DEFAULT 'VE',
    estado_geo_id    uuid REFERENCES estados(id),   -- geographic focus, if any
    organizacion_id  uuid REFERENCES organizaciones(id), -- owning org (for official channels)
    credibilidad     smallint NOT NULL DEFAULT 50 CHECK (credibilidad BETWEEN 0 AND 100),
    sesgo            text,                          -- documented editorial leaning (optional)
    verificada       boolean NOT NULL DEFAULT false,
    frecuencia_min   integer NOT NULL DEFAULT 360,  -- polling cadence in minutes
    robots_ok        boolean NOT NULL DEFAULT true, -- crawling permitted per robots/ToS
    ultima_lectura   timestamptz,
    ultimo_error     text,
    notas            text,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_fuentes_updated BEFORE UPDATE ON fuentes
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE INDEX idx_fuentes_estado ON fuentes(estado);
CREATE INDEX idx_fuentes_tipo ON fuentes(tipo);

-- ============================================================================
--  TOPICS
-- ============================================================================

CREATE TABLE temas (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre       text NOT NULL UNIQUE,
    slug         text NOT NULL UNIQUE,
    categoria    text,                    -- 'economia','seguridad','elecciones',...
    palabras_clave text[] NOT NULL DEFAULT '{}',
    color        text DEFAULT '#6366f1',
    activo       boolean NOT NULL DEFAULT true,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
--  ARTICLES (ingested public items) + classification & relations
-- ============================================================================

CREATE TABLE articulos (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fuente_id       uuid NOT NULL REFERENCES fuentes(id) ON DELETE CASCADE,
    url             text NOT NULL,
    url_hash        text NOT NULL UNIQUE,            -- dedupe key (sha256 of normalized url)
    titulo          text NOT NULL,
    resumen         text,
    contenido       text,
    autor           text,
    idioma          text NOT NULL DEFAULT 'es',
    imagen_url      text,
    publicado_en    timestamptz,
    ingerido_en     timestamptz NOT NULL DEFAULT now(),
    estado          estado_articulo NOT NULL DEFAULT 'crudo',
    relevancia      nivel_relevancia NOT NULL DEFAULT 'media',
    alcance_estimado integer,                        -- estimated reach (followers/visits proxy)
    estado_geo_id   uuid REFERENCES estados(id),
    municipio_id    uuid REFERENCES municipios(id),
    tema_id         uuid REFERENCES temas(id),
    metadatos       jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_articulos_updated BEFORE UPDATE ON articulos
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE INDEX idx_articulos_publicado ON articulos(publicado_en DESC);
CREATE INDEX idx_articulos_fuente ON articulos(fuente_id);
CREATE INDEX idx_articulos_estado ON articulos(estado);
CREATE INDEX idx_articulos_tema ON articulos(tema_id);
CREATE INDEX idx_articulos_geo ON articulos(estado_geo_id);
CREATE INDEX idx_articulos_titulo_trgm ON articulos USING gin (titulo gin_trgm_ops);
-- Full-text search vector (Spanish).
-- NOTE: unaccent() is STABLE (not IMMUTABLE), so it cannot be used inside a
-- GENERATED column. The 'spanish' configuration already handles stemming; for
-- accent-insensitive search use the pg_trgm index on titulo or an IMMUTABLE
-- unaccent wrapper at query time.
ALTER TABLE articulos ADD COLUMN IF NOT EXISTS tsv tsvector
    GENERATED ALWAYS AS (
        to_tsvector('spanish', coalesce(titulo,'') || ' ' || coalesce(resumen,''))
    ) STORED;
CREATE INDEX idx_articulos_tsv ON articulos USING gin (tsv);

-- Mentions: link an article to an actor and/or organization (the analytic core)
CREATE TABLE menciones (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    articulo_id     uuid NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
    actor_id        uuid REFERENCES actores(id) ON DELETE CASCADE,
    organizacion_id uuid REFERENCES organizaciones(id) ON DELETE CASCADE,
    fragmento       text,                  -- matched snippet (public text)
    peso            real NOT NULL DEFAULT 1.0,   -- weight/prominence in the article
    created_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (actor_id IS NOT NULL OR organizacion_id IS NOT NULL)
);
CREATE INDEX idx_menciones_articulo ON menciones(articulo_id);
CREATE INDEX idx_menciones_actor ON menciones(actor_id);
CREATE INDEX idx_menciones_org ON menciones(organizacion_id);

-- Sentiment analysis results (AI / lexicon), per article (optionally per mention)
CREATE TABLE analisis_sentimiento (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    articulo_id   uuid NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
    mencion_id    uuid REFERENCES menciones(id) ON DELETE CASCADE,
    etiqueta      sentimiento NOT NULL,
    score         real NOT NULL CHECK (score BETWEEN -1 AND 1),
    confianza     real NOT NULL DEFAULT 0.5 CHECK (confianza BETWEEN 0 AND 1),
    emociones     jsonb NOT NULL DEFAULT '{}'::jsonb,   -- {alegria,enojo,miedo,...}
    modelo        text NOT NULL DEFAULT 'local-lexicon',
    created_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_sentimiento_articulo ON analisis_sentimiento(articulo_id);
CREATE INDEX idx_sentimiento_etiqueta ON analisis_sentimiento(etiqueta);

-- ============================================================================
--  NARRATIVES (clustered themes / framing across articles)
-- ============================================================================

CREATE TABLE narrativas (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo        text NOT NULL,
    descripcion   text,
    palabras_clave text[] NOT NULL DEFAULT '{}',
    tema_id       uuid REFERENCES temas(id),
    sentimiento   sentimiento,
    relevancia    nivel_relevancia NOT NULL DEFAULT 'media',
    emergente     boolean NOT NULL DEFAULT false,
    primera_vista timestamptz,
    ultima_vista  timestamptz,
    total_articulos integer NOT NULL DEFAULT 0,
    alcance_estimado bigint NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_narrativas_updated BEFORE UPDATE ON narrativas
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE narrativa_articulos (
    narrativa_id  uuid NOT NULL REFERENCES narrativas(id) ON DELETE CASCADE,
    articulo_id   uuid NOT NULL REFERENCES articulos(id) ON DELETE CASCADE,
    similitud     real NOT NULL DEFAULT 0.0,
    PRIMARY KEY (narrativa_id, articulo_id)
);

-- ============================================================================
--  TRENDS (daily aggregated time-series for charts / comparisons)
-- ============================================================================

CREATE TABLE tendencias (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha           date NOT NULL,
    tema_id         uuid REFERENCES temas(id),
    actor_id        uuid REFERENCES actores(id),
    organizacion_id uuid REFERENCES organizaciones(id),
    estado_geo_id   uuid REFERENCES estados(id),
    menciones       integer NOT NULL DEFAULT 0,
    alcance_estimado bigint NOT NULL DEFAULT 0,
    sentimiento_prom real NOT NULL DEFAULT 0,        -- avg score [-1,1]
    variacion_pct   real,                            -- vs previous period
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (fecha, tema_id, actor_id, organizacion_id, estado_geo_id)
);
CREATE INDEX idx_tendencias_fecha ON tendencias(fecha DESC);
CREATE INDEX idx_tendencias_actor ON tendencias(actor_id);
CREATE INDEX idx_tendencias_tema ON tendencias(tema_id);

-- Daily KPI snapshots powering the Executive Dashboard cards
CREATE TABLE kpi_snapshots (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha                date NOT NULL UNIQUE,
    total_articulos      integer NOT NULL DEFAULT 0,
    total_menciones      integer NOT NULL DEFAULT 0,
    fuentes_activas      integer NOT NULL DEFAULT 0,
    sentimiento_global   real NOT NULL DEFAULT 0,
    narrativas_activas   integer NOT NULL DEFAULT 0,
    narrativas_emergentes integer NOT NULL DEFAULT 0,
    alertas_abiertas     integer NOT NULL DEFAULT 0,
    alcance_total        bigint NOT NULL DEFAULT 0,
    detalle              jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at           timestamptz NOT NULL DEFAULT now()
);

-- ============================================================================
--  ALERTS (early-warning system)
-- ============================================================================

CREATE TABLE alertas (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo        text NOT NULL,
    descripcion   text,
    tipo          text NOT NULL,           -- 'pico_menciones','narrativa_emergente','sentimiento',...
    severidad     severidad_alerta NOT NULL DEFAULT 'media',
    estado        estado_alerta NOT NULL DEFAULT 'abierta',
    tema_id       uuid REFERENCES temas(id),
    actor_id      uuid REFERENCES actores(id),
    estado_geo_id uuid REFERENCES estados(id),
    narrativa_id  uuid REFERENCES narrativas(id),
    umbral        jsonb NOT NULL DEFAULT '{}'::jsonb,    -- rule that triggered it
    valor         real,                    -- observed value
    asignada_a    uuid REFERENCES usuarios(id),
    reconocida_en timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_alertas_updated BEFORE UPDATE ON alertas
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE INDEX idx_alertas_estado ON alertas(estado);
CREATE INDEX idx_alertas_severidad ON alertas(severidad);
CREATE INDEX idx_alertas_created ON alertas(created_at DESC);

-- ============================================================================
--  REPORTS (PDF only — the sole permitted export format)
-- ============================================================================

CREATE TABLE reportes (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo        text NOT NULL,
    tipo          text NOT NULL DEFAULT 'ejecutivo_diario', -- ejecutivo_diario | semanal | ad_hoc
    periodo_desde date,
    periodo_hasta date,
    estado        estado_reporte NOT NULL DEFAULT 'generando',
    archivo_path  text,                    -- storage path of the generated PDF
    archivo_bytes bigint,
    pdf_sha256    text,                    -- integrity hash
    resumen       text,                    -- AI-generated executive summary (cached)
    parametros    jsonb NOT NULL DEFAULT '{}'::jsonb,
    generado_por  uuid REFERENCES usuarios(id),
    created_at    timestamptz NOT NULL DEFAULT now(),
    completado_en timestamptz
);
CREATE INDEX idx_reportes_periodo ON reportes(periodo_hasta DESC);
CREATE INDEX idx_reportes_tipo ON reportes(tipo);

-- ============================================================================
--  ETL ORCHESTRATION (observability of automated daily pipeline)
-- ============================================================================

CREATE TABLE etl_ejecuciones (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    job           text NOT NULL,           -- 'ingest','clean','classify','analyze','aggregate'
    estado        estado_etl NOT NULL DEFAULT 'en_cola',
    fuente_id     uuid REFERENCES fuentes(id) ON DELETE SET NULL,
    items_in      integer NOT NULL DEFAULT 0,
    items_out     integer NOT NULL DEFAULT 0,
    items_error   integer NOT NULL DEFAULT 0,
    duracion_ms   integer,
    log           text,
    iniciado_en   timestamptz NOT NULL DEFAULT now(),
    finalizado_en timestamptz
);
CREATE INDEX idx_etl_iniciado ON etl_ejecuciones(iniciado_en DESC);
CREATE INDEX idx_etl_job ON etl_ejecuciones(job);

-- ============================================================================
--  VIEWS (convenience aggregations for the API / dashboard)
-- ============================================================================

-- Actor ranking by mentions in the last 30 days (with avg sentiment)
CREATE OR REPLACE VIEW v_ranking_actores AS
SELECT a.id, a.nombre, a.cargo, o.siglas AS organizacion,
       count(m.id)                                   AS menciones,
       coalesce(avg(s.score), 0)                     AS sentimiento_prom,
       coalesce(sum(art.alcance_estimado), 0)        AS alcance_estimado
FROM actores a
LEFT JOIN menciones m  ON m.actor_id = a.id
LEFT JOIN articulos art ON art.id = m.articulo_id
       AND art.publicado_en >= now() - interval '30 days'
LEFT JOIN analisis_sentimiento s ON s.articulo_id = art.id
LEFT JOIN organizaciones o ON o.id = a.organizacion_id
WHERE a.activo
GROUP BY a.id, a.nombre, a.cargo, o.siglas
ORDER BY menciones DESC;

-- Territorial summary: article volume + sentiment by state (last 30 days)
CREATE OR REPLACE VIEW v_resumen_territorial AS
SELECT e.id, e.nombre AS estado, e.latitud, e.longitud,
       count(art.id)               AS articulos,
       coalesce(avg(s.score), 0)   AS sentimiento_prom
FROM estados e
LEFT JOIN articulos art ON art.estado_geo_id = e.id
       AND art.publicado_en >= now() - interval '30 days'
LEFT JOIN analisis_sentimiento s ON s.articulo_id = art.id
GROUP BY e.id, e.nombre, e.latitud, e.longitud;

-- ============================================================================
--  ROW-LEVEL SECURITY (Supabase) — enable & define per deployment.
--  Example below; full policies live in database/migrations & DEPLOYMENT.md.
-- ============================================================================
-- ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY reportes_read ON reportes FOR SELECT
--   USING ( auth.role() IN ('admin','analista','editor','lector') );

-- ============================================================================
--  NOTE on citext: the extension is enabled at the top of this file (required
--  before usuarios.email). If unavailable in some environment, replace `citext`
--  with `text` + a UNIQUE lower(email) index. Supabase ships citext.
-- ============================================================================
