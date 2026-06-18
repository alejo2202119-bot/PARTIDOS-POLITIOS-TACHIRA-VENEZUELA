# Manual Técnico — Venezuela Political Intelligence Dashboard (VPID)

> **Alcance del sistema:** VPID analiza **únicamente información pública y abiertamente
> disponible** (medios publicados, RSS, comunicados oficiales y APIs públicas
> autorizadas) sobre actores, partidos, medios y narrativas políticas de Venezuela,
> para usos legítimos (periodismo, investigación académica, observación electoral y
> análisis de sociedad civil). Consulte la [Política de Uso Ético y Legal](USO_ETICO.md).

Este documento es la guía técnica para instalar, configurar, operar y extender VPID.
Para la visión arquitectónica (componentes, flujo de datos, modelo de datos y
decisiones tecnológicas) consulte [ARQUITECTURA.md](ARQUITECTURA.md); para el contrato
REST, [API.md](API.md); y para el despliegue en producción, [DESPLIEGUE.md](DESPLIEGUE.md).

## Tabla de contenidos

1. [Pila tecnológica](#1-pila-tecnológica)
2. [Árbol del proyecto](#2-árbol-del-proyecto)
3. [Requisitos](#3-requisitos)
4. [Instalación paso a paso](#4-instalación-paso-a-paso)
5. [Configuración: todas las claves de `.env`](#5-configuración-todas-las-claves-de-env)
6. [El modo DEMO (degradación elegante)](#6-el-modo-demo-degradación-elegante)
7. [Motores de análisis y pipeline ETL](#7-motores-de-análisis-y-pipeline-etl)
8. [Servicios de aplicación](#8-servicios-de-aplicación)
9. [Pruebas](#9-pruebas)
10. [Estilo de código (ruff)](#10-estilo-de-código-ruff)
11. [Cómo extender el sistema](#11-cómo-extender-el-sistema)
12. [Resolución de problemas](#12-resolución-de-problemas)
13. [Documentos relacionados](#13-documentos-relacionados)

---

## 1. Pila tecnológica

| Capa | Tecnología |
|------|-----------|
| API | FastAPI 0.115 · SQLAlchemy 2.0 async + asyncpg · Pydantic v2 / pydantic-settings |
| Autenticación | JWT (`python-jose`) + hash `bcrypt` (`passlib`) · RBAC jerárquico |
| Caché | Redis (`redis.asyncio`) |
| ETL | APScheduler · `httpx` + `feedparser` (ingesta RSS/Atom) |
| Análisis | Léxico de sentimiento propio (stdlib) · proveedor de IA opcional (`anthropic`) |
| PDF | `reportlab` + `matplotlib` (gráfico de evolución) |
| Base de datos | PostgreSQL 15+ / Supabase (extensiones `pgcrypto`, `pg_trgm`, `unaccent`, `citext`) |
| Frontend | HTML5/CSS3/JS *vanilla* + Tailwind CSS + ApexCharts + Chart.js + Leaflet |
| Servidor web | nginx (estáticos + *reverse proxy* a `/api/`) |

Versiones exactas del backend en [`backend/requirements.txt`](../backend/requirements.txt).
Python objetivo: **3.11** (`backend/pyproject.toml`).

---

## 2. Árbol del proyecto

```
PARTIDOS-POLITIOS-TACHIRA-VENEZUELA/
├── backend/                     # API FastAPI + motor de análisis + ETL
│   ├── app/
│   │   ├── main.py              # App FastAPI, middleware, /health, / (raíz)
│   │   ├── config.py            # Settings (pydantic-settings, espeja .env)
│   │   ├── database.py          # Engine/sesiones async (lazy; ping; dispose)
│   │   ├── models.py            # ORM SQLAlchemy (espeja database/schema.sql)
│   │   ├── schemas.py           # Modelos Pydantic (Page, auth, fuentes, reportes…)
│   │   ├── api/
│   │   │   ├── router.py        # Monta todos los routers bajo /api/v1
│   │   │   └── routes/          # Un módulo por grupo de endpoints
│   │   │       ├── auth.py        dashboard.py   news.py      trends.py
│   │   │       ├── narratives.py  sentiment.py   actors.py    territorial.py
│   │   │       └── alerts.py      sources.py     reports.py   search.py   etl.py
│   │   ├── core/
│   │   │   ├── security.py      # Hash, JWT, get_current_user, require_role (RBAC)
│   │   │   ├── cache.py         # Redis async + @cached (no-op si Redis cae)
│   │   │   ├── audit.py         # Bitácora best-effort en tabla auditoria
│   │   │   └── demo_data.py     # Dataset de demostración (modo DEMO)
│   │   ├── etl/
│   │   │   ├── rss_ingest.py    # Etapa 1: ingest (RSS/Atom)
│   │   │   ├── clean.py         # Etapa 2: clean (normaliza/limpia)
│   │   │   ├── classify.py      # Etapa 3: classify (tema/geo/relevancia)
│   │   │   ├── analyze.py       # Etapa 4: analyze (sentimiento + menciones)
│   │   │   ├── aggregate.py     # Etapa 5: aggregate (tendencias/KPIs/alertas)
│   │   │   ├── pipeline.py      # Orquestador del pipeline + informe diario
│   │   │   └── scheduler.py     # APScheduler (--once para una ejecución)
│   │   └── services/
│   │       ├── sentiment.py     # Sentimiento léxico/IA
│   │       ├── narratives.py    # Clustering por solapamiento de keywords
│   │       ├── trends.py        # Crecimiento %, emergentes, alcance
│   │       ├── alerts_engine.py # Motor de alertas por reglas
│   │       └── pdf_report.py    # Generación del Informe Ejecutivo (reportlab)
│   ├── tests/                   # pytest (corren sin DB/Redis gracias al modo DEMO)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml           # Config de ruff + pytest
│   └── README.md
├── frontend/                    # SPA estática (12 módulos)
│   ├── index.html               # Shell: login, sidebar, topbar, ⌘K, tema, filtros
│   └── assets/
│       ├── css/styles.css
│       ├── img/logo.svg
│       └── js/
│           ├── config.js        # apiBase, navegación (12 módulos), formateadores
│           ├── api.js           # Cliente API (live → fallback demo mock.js)
│           ├── views.js         # Renderizadores de los 12 módulos
│           ├── charts.js        # ApexCharts/Chart.js
│           ├── maps.js          # Leaflet
│           ├── theme.js         # Modo claro/oscuro
│           ├── app.js           # Router por hash, login, ⌘K, drawer de alertas
│           └── data/mock.js     # Dataset de demostración del frontend
├── database/
│   ├── schema.sql               # Esquema canónico (fuente de verdad)
│   ├── seed.sql                 # Roles, geografía, organizaciones, fuentes, temas, demo
│   └── migrations/0001_initial.sql   # Puntero a schema.sql + seed.sql
├── deploy/
│   └── nginx.conf               # Estáticos + proxy /api/ → backend:8000
├── docs/
│   ├── ARQUITECTURA.md   API.md   MANUAL_TECNICO.md
│   ├── MANUAL_USUARIO.md DESPLIEGUE.md   USO_ETICO.md
├── storage/
│   └── reports/                 # PDFs generados (.gitkeep)
├── docker-compose.yml           # Stack local/staging: db, redis, backend, etl, frontend
├── .env.example                 # Contrato de configuración
└── README.md
```

---

## 3. Requisitos

| Componente | Versión mínima | Notas |
|-----------|----------------|-------|
| **Python** | 3.11+ | Backend y ETL. |
| **PostgreSQL** | 15+ (o Supabase) | Requiere `pgcrypto`, `pg_trgm`, `unaccent`, `citext`. |
| **Redis** | 7+ (recomendado) | Caché. **Opcional**: si no está, la caché se desactiva sola. |
| **Node.js** | LTS (opcional) | Solo para tooling de frontend; el frontend no requiere *build* (Tailwind/ApexCharts/Chart.js/Leaflet se cargan por CDN). |
| **nginx** | 1.27+ | Sirve los estáticos y hace de *reverse proxy* a la API. |
| **Docker / Docker Compose** | reciente | Vía recomendada para levantar todo el stack local. |

> **Nota:** gracias al [modo DEMO](#6-el-modo-demo-degradación-elegante), el backend
> arranca y es explorable **sin** PostgreSQL ni Redis. Estos son obligatorios solo en
> producción (`APP_ENV=production`).

---

## 4. Instalación paso a paso

### 4.1 Clonar y preparar variables

```bash
git clone <repo-url> PARTIDOS-POLITIOS-TACHIRA-VENEZUELA
cd PARTIDOS-POLITIOS-TACHIRA-VENEZUELA
cp .env.example .env          # editar y poner valores reales (ver §5)
```

### 4.2 Base de datos (PostgreSQL)

Aplique el esquema canónico y los datos de referencia, **en este orden**:

```bash
# Crear la base y el usuario (ajuste a su entorno)
createdb vpid
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/seed.sql
```

Alternativamente, con un *runner* de migraciones use el puntero
[`database/migrations/0001_initial.sql`](../database/migrations/0001_initial.sql),
que ejecuta `schema.sql` y `seed.sql` en orden.

El `seed.sql` crea: roles, el usuario admin por defecto, los 24 estados de Venezuela,
los 29 municipios de Táchira, organizaciones y figuras públicas de referencia, las
fuentes verificables, los temas y un conjunto **sintético** de artículos/menciones/
sentimiento para demostrar el dashboard.

> **Usuario admin por defecto:** `admin@vpid.local` / `ChangeMe!2026`.
> **Debe cambiarse en el primer acceso.** El hash bcrypt vive en `seed.sql`.

### 4.3 Backend (API con uvicorn)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Arranque en desarrollo (autorecarga)
uvicorn app.main:app --reload --port 8000
#   API:     http://localhost:8000/api/v1
#   Swagger: http://localhost:8000/api/docs
#   ReDoc:   http://localhost:8000/api/redoc
#   Health:  http://localhost:8000/health
```

Para varios *workers* (sin recarga):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4.4 ETL (worker programado)

El ETL es un **proceso independiente** del API.

```bash
cd backend
source .venv/bin/activate

# Demonio: programa el pipeline (ETL_SCHEDULE_CRON) y el informe (REPORT_DAILY_CRON)
python -m app.etl.scheduler

# Una sola pasada (pipeline completo + informe) y salir — útil para cron/manual:
python -m app.etl.scheduler --once
```

El planificador usa `APP_TIMEZONE` (por defecto `America/Caracas`). Los crons por
defecto son `0 5 * * *` (ETL, 05:00) y `0 6 * * *` (informe, 06:00).

### 4.5 Frontend

El frontend es **estático**: no requiere compilación. Dos opciones:

```bash
# A) Servido por nginx con proxy de API (recomendado, igual que producción)
#    Use deploy/nginx.conf (sirve frontend/ y proxya /api/ → backend:8000).

# B) Servidor estático simple para desarrollo rápido
cd frontend
python -m http.server 5173
#   Abrir http://localhost:5173
```

Configure `apiBase` en [`frontend/assets/js/config.js`](../frontend/assets/js/config.js)
si el API no está en `/api/v1` del mismo origen. Recuerde alinear `FRONTEND_ORIGIN`
en `.env` para el CORS del backend.

### 4.6 Todo junto con Docker Compose (la vía más rápida)

```bash
cp .env.example .env          # imprescindible: docker-compose usa env_file: .env
docker compose up -d --build
```

Esto levanta cinco servicios (ver [DESPLIEGUE.md](DESPLIEGUE.md#2-puesta-en-marcha-rápida-docker-compose)):

| Servicio | Imagen / build | Puerto host | Función |
|----------|----------------|-------------|---------|
| `db` | `postgres:15-alpine` | 5432 | Inicializa `schema.sql` + `seed.sql` automáticamente. |
| `redis` | `redis:7-alpine` | 6379 | Caché (con AOF `--appendonly yes`). |
| `backend` | `./backend` | 8000 | `uvicorn app.main:app --workers 2`. |
| `etl` | `./backend` | — | `python -m app.etl.scheduler` (demonio). |
| `frontend` | `nginx:1.27-alpine` | 8080 | Sirve `frontend/` + proxy `/api/`. |

Acceda a la app en `http://localhost:8080`.

---

## 5. Configuración: todas las claves de `.env`

El backend carga la configuración con `pydantic-settings`
([`backend/app/config.py`](../backend/app/config.py)), que **espeja exactamente** el
contrato de [`.env.example`](../.env.example). Las claves no presentes toman su valor
por defecto. A continuación, **todas** las claves documentadas.

### 5.1 Aplicación

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `APP_NAME` | `Venezuela Political Intelligence Dashboard` | Nombre mostrado en OpenAPI y la raíz `/`. |
| `APP_ENV` | `development` | `development` \| `staging` \| `production`. Controla el modo DEMO (ver §6). |
| `APP_DEBUG` | `true` | Nivel de log `DEBUG` si es `true`, `INFO` si no. |
| `APP_HOST` | `0.0.0.0` | Host de escucha (informativo; uvicorn recibe `--host`). |
| `APP_PORT` | `8000` | Puerto de escucha (informativo; uvicorn recibe `--port`). |
| `APP_TIMEZONE` | `America/Caracas` | Zona horaria del planificador APScheduler. |
| `APP_DEFAULT_LOCALE` | `es` | Idioma por defecto de la plataforma. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Origen(es) permitido(s) por CORS (lista separada por comas → `cors_origins`). |

### 5.2 Base de datos (PostgreSQL)

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `POSTGRES_HOST` | `localhost` | Host de Postgres. |
| `POSTGRES_PORT` | `5432` | Puerto de Postgres. |
| `POSTGRES_DB` | `vpid` | Nombre de la base de datos. |
| `POSTGRES_USER` | `vpid_app` | Usuario de aplicación. |
| `POSTGRES_PASSWORD` | `change_me_strong_password` | Contraseña del usuario. **Cámbiela.** |
| `DATABASE_URL` | `postgresql+asyncpg://vpid_app:change_me_strong_password@localhost:5432/vpid` | URL completa SQLAlchemy async. **Tiene prioridad** sobre las partes anteriores; es la que usa el engine. |

### 5.3 Supabase (opcional; solo del lado servidor)

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `SUPABASE_URL` | *(vacío)* | URL del proyecto Supabase. |
| `SUPABASE_ANON_KEY` | *(vacío)* | Clave pública (anon) de Supabase. |
| `SUPABASE_SERVICE_ROLE_KEY` | *(vacío)* | Clave de servicio. **SECRETO — nunca en el frontend.** |

### 5.4 Seguridad / Autenticación

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `JWT_SECRET_KEY` | `generate_a_64_char_random_secret` | Secreto de firma JWT. **Genere uno aleatorio de 64+ caracteres.** |
| `JWT_ALGORITHM` | `HS256` | Algoritmo de firma del token. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Expiración del *access token* (minutos). |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Expiración del *refresh token* (días). |
| `PASSWORD_HASH_SCHEME` | `bcrypt` | Esquema de hash de contraseñas. |

### 5.5 Caché (Redis)

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | URL de conexión a Redis. |
| `CACHE_TTL_SECONDS` | `300` | TTL por defecto de las entradas de caché (segundos). |

### 5.6 IA / NLP

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `AI_PROVIDER` | `local` | `local` (léxico, sin clave) \| `anthropic` \| `openai`. Selecciona el motor de sentimiento. |
| `ANTHROPIC_API_KEY` | *(vacío)* | Clave del proveedor Anthropic. Si está vacía, se usa el léxico local aunque `AI_PROVIDER=anthropic`. |
| `ANTHROPIC_MODEL` | `claude-opus-4-8` | Modelo Anthropic empleado para la puntuación de sentimiento. |
| `AI_SENTIMENT_BATCH_SIZE` | `25` | Tamaño de lote para el análisis de sentimiento. |

### 5.7 ETL / Ingesta

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `ETL_SCHEDULE_CRON` | `0 5 * * *` | Cron del pipeline diario (05:00 en `APP_TIMEZONE`). |
| `ETL_USER_AGENT` | `VPID-OSINT-Bot/1.0 (+public-sources-only)` | User-Agent identificado del bot de ingesta. |
| `ETL_REQUEST_TIMEOUT` | `20` | Timeout HTTP por solicitud (segundos). |
| `ETL_MAX_ARTICLES_PER_SOURCE` | `200` | Máximo de artículos por fuente y ejecución. |
| `ETL_RESPECT_ROBOTS_TXT` | `true` | Si es `true`, omite fuentes con `robots_ok = false` (respeto de robots.txt/ToS). |

### 5.8 Informes (PDF)

| Clave | Valor por defecto | Descripción |
|-------|-------------------|-------------|
| `REPORTS_STORAGE_PATH` | `./storage/reports` | Carpeta donde se persisten los PDFs generados. |
| `REPORT_DAILY_CRON` | `0 6 * * *` | Cron del informe diario (06:00, tras el ETL). |
| `REPORT_BRAND_NAME` | `Venezuela Political Intelligence` | Marca/autor incrustada en el PDF. |
| `REPORT_LOGO_PATH` | `./frontend/assets/img/logo.svg` | Ruta del logotipo para el informe. |

### 5.9 Metadatos internos (no en `.env`)

Definidos con valores sensatos en `config.py`, no se leen del entorno:

| Clave | Valor | Descripción |
|-------|-------|-------------|
| `API_V1_PREFIX` | `/api/v1` | Prefijo del router versionado. |
| `VERSION` | `1.0.0` | Versión de la app (OpenAPI, `/health`). |
| `DEMO_MODE` | *(calculado)* | `true` cuando `APP_ENV != production`. |
| `cors_origins` | *(calculado)* | Lista derivada de `FRONTEND_ORIGIN`. |

---

## 6. El modo DEMO (degradación elegante)

`DEMO_MODE` es un campo **calculado**: vale `true` siempre que `APP_ENV` no sea
`production`. Su objetivo es que la plataforma **siempre arranque y sea explorable**,
incluso sin base de datos ni Redis.

| Comportamiento | En DEMO (`development`/`staging`) | En `production` |
|----------------|-----------------------------------|-----------------|
| Endpoints de lectura | Si la BD está vacía/inaccesible, responden con `app/core/demo_data.py`. | Requieren BD real. |
| Login (`/auth/login`) | Cualquier credencial inicia sesión como `admin` (demo). | Valida contra `usuarios` o devuelve `401`. |
| `get_current_user` sin token | Devuelve un admin de demostración. | Devuelve `401 No autenticado`. |
| `require_role(...)` (RBAC) | No bloquea (deja pasar). | Aplica jerarquía de roles (`403` si falta permiso). |
| Caché Redis | No-op si Redis no responde. | No-op si Redis no responde (también degrada). |

> **Importante:** las cifras del dataset de demostración (`demo_data.py` y el bloque
> sintético de `seed.sql`) son **sintéticas e ilustrativas**, no mediciones reales.

El estado actual se ve en `GET /health` (`demo_mode`, `db`, `cache`) y en la insignia
de conexión del frontend (`live` / `demo`).

---

## 7. Motores de análisis y pipeline ETL

El pipeline diario sigue cinco etapas y, al final, genera el informe. Cada transición
se refleja en `articulos.estado` (`crudo → limpio → clasificado → analizado`; o
`descartado`). Orquestación en [`app/etl/pipeline.py`](../backend/app/etl/pipeline.py).

```
ingest → clean → classify → analyze → aggregate → (report PDF)
```

| Etapa | Módulo | Entrada → Salida | Qué hace |
|-------|--------|------------------|----------|
| **1. Ingest** | `etl/rss_ingest.py` | Fuentes → artículos `crudo` | Descarga feeds RSS/Atom (`httpx` + `feedparser`); deduplica por `url_hash` (SHA-256 de la URL normalizada); respeta `robots_ok` y `ETL_MAX_ARTICLES_PER_SOURCE`; se identifica con `ETL_USER_AGENT`. |
| **2. Clean** | `etl/clean.py` | `crudo` → `limpio` | Quita HTML, colapsa espacios, detecta idioma (heurístico; por defecto `es`). |
| **3. Classify** | `etl/classify.py` | `limpio` → `clasificado` | Asigna tema por palabras clave (`TOPIC_KEYWORDS`, espeja `temas` del seed), geolocaliza por nombre de estado y calcula relevancia (`critica`/`alta`/`media`/`baja`). |
| **4. Analyze** | `etl/analyze.py` | `clasificado` → `analizado` | Ejecuta el servicio de sentimiento por artículo y extrae menciones de actores (nombre + `aliases`). |
| **5. Aggregate** | `etl/aggregate.py` | `analizado` → resumen | Cuenta por tema/estado, calcula sentimiento global y alcance, arma un *snapshot* de KPIs y evalúa el motor de alertas. |
| **Report** | `services/pdf_report.py` | agregados → PDF | Genera el Informe Ejecutivo y lo registra/persiste. |

**Observabilidad:** cada etapa se cronometra y se registra (best-effort) en
`etl_ejecuciones` mediante `pipeline._record(...)`. Si la BD no está disponible, el
evento se escribe al log de la aplicación. El endpoint `GET /api/v1/etl/estado`
expone las últimas ejecuciones y el próximo ciclo programado.

**Planificación:** [`app/etl/scheduler.py`](../backend/app/etl/scheduler.py) usa
`AsyncIOScheduler` con dos `CronTrigger`: `etl_pipeline` (`ETL_SCHEDULE_CRON`) y
`daily_report` (`REPORT_DAILY_CRON`), ambos en `APP_TIMEZONE`. Con `--once` ejecuta
`run_full()` y luego `run_daily_report()` una sola vez.

---

## 8. Servicios de aplicación

Ubicados en [`backend/app/services/`](../backend/app/services/).

### 8.1 Sentimiento — `sentiment.py`

- **Proveedor por defecto `local`:** puntuador léxico en español sin dependencias.
  Normaliza el texto (minúsculas, sin acentos, tokeniza), cuenta términos de los
  conjuntos `_POSITIVE`/`_NEGATIVE` y calcula `score = (pos − neg) / (pos + neg)` en
  el rango `[-1, 1]`. La `confianza` crece con la proporción de tokens con polaridad.
  Etiqueta: `positivo` si `score > 0.15`, `negativo` si `< −0.15`, si no `neutral`.
  Deriva además emociones (`alegria`, `enojo`, `miedo`, `tristeza`) por coincidencia
  de palabras clave.
- **Proveedor `anthropic` (opcional):** `analyze_with_anthropic` usa la API de
  mensajes de Anthropic (modelo `ANTHROPIC_MODEL`) pidiendo **solo JSON**. Si no hay
  `ANTHROPIC_API_KEY` o falla, **cae automáticamente** al léxico local.
- Punto de entrada: `await analyze(texto)` → `SentimentResult`
  (`etiqueta`, `score`, `confianza`, `emociones`, `modelo`). Lo usan la etapa
  `analyze` del ETL y el endpoint `POST /api/v1/sentimiento/analizar`.

### 8.2 Narrativas — `narratives.py`

Detección por **solapamiento de palabras clave** (clustering ligero). Extrae el
conjunto de keywords de cada artículo (descartando *stop-words*), agrupa artículos
cuya **similitud de Jaccard** supera un umbral (`threshold = 0.28`) y marca como
**emergente** todo grupo con `total_articulos ≥ 3` (heurística refinada en
`aggregate`). Devuelve `titulo`, `palabras_clave`, `total_articulos`,
`alcance_estimado`, `miembros` y `emergente`.

### 8.3 Tendencias — `trends.py`

Funciones de agregación: `growth_pct(actual, previo)` (variación porcentual segura
ante ceros), `aggregate_daily(...)` (series diarias por clave), `emerging(...)`
(ranking por crecimiento de la última ventana vs. la previa) y `estimated_reach(...)`
(suma de `alcance_estimado`).

### 8.4 Motor de alertas — `alerts_engine.py`

Reglas **transparentes y configurables** (`DEFAULT_RULES`) evaluadas sobre las
métricas agregadas. Emite alertas con `severidad` graduada (`_sev`):

| Regla | Umbral por defecto | Tipo de alerta |
|-------|--------------------|----------------|
| Pico de menciones | `+100%` día contra día | `pico_menciones` |
| Caída de sentimiento | `−0.15` (caída absoluta del score) | `sentimiento` |
| Narrativa emergente | `+80%` de crecimiento | `narrativa_emergente` |
| Concentración territorial | `60%` de la cobertura en un estado | `territorial` |

### 8.5 Informe PDF — `pdf_report.py`

Construye el **Informe Ejecutivo** con `reportlab`. Secciones: portada institucional,
fecha de generación, resumen ejecutivo, tabla de KPIs, gráfico de evolución por tema
(PNG con `matplotlib`), actores más mencionados, narrativas predominantes, análisis
territorial, alertas relevantes y conclusiones/recomendaciones generadas
automáticamente. Funciones clave:

- `build_pdf(...)` → `bytes` del PDF.
- `generate_and_store(...)` → construye, persiste en `REPORTS_STORAGE_PATH`
  (`informe_ejecutivo_YYYYMMDD.pdf`) y devuelve metadatos
  (`archivo_path`, `archivo_bytes`, `pdf_sha256`, `completado_en`).

> **PDF es el único formato de exportación de toda la plataforma.** No se generan
> Excel, CSV ni Word (ver [ARQUITECTURA.md §9](ARQUITECTURA.md#9-decisiones-tecnológicas-y-compromisos)).

### 8.6 Núcleo (`core/`)

- `security.py`: hash/verificación bcrypt; creación y decodificación de JWT;
  `get_current_user`; `require_role(*roles)` con jerarquía
  `lector(0) < editor(1) < analista(2) < admin(3)`.
- `cache.py`: cliente Redis async + decorador `@cached(ttl, key)`; si Redis no está,
  se convierte en *no-op*.
- `audit.py`: `log(accion, ...)` escribe en `auditoria` (o al log si la BD no está);
  **nunca lanza excepción**.
- `demo_data.py`: dataset representativo en memoria que alimenta los endpoints de
  lectura en modo DEMO.

---

## 9. Pruebas

Las pruebas usan `pytest` y un `TestClient` de FastAPI que **funciona sin BD ni
Redis** (modo DEMO; ver `tests/conftest.py`, que fija `APP_ENV=development`).

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Suite actual: `tests/test_health.py` (sonda `/health`), `tests/test_demo_data.py`
(integridad del dataset de demostración) y `tests/test_sentiment.py` (puntuador
léxico). Configuración de pytest en `pyproject.toml` (`asyncio_mode = "auto"`,
`testpaths = ["tests"]`, `addopts = "-q"`).

---

## 10. Estilo de código (ruff)

El proyecto usa **ruff** para *lint* y formato (config en `backend/pyproject.toml`):

```bash
cd backend
ruff check .          # lint
ruff format .         # formateo
ruff check --fix .    # correcciones automáticas
```

Parámetros relevantes: `line-length = 100`, `target-version = "py311"`. Reglas
seleccionadas: `E`, `F`, `I` (isort), `UP` (pyupgrade), `B` (bugbear), `C4`, `SIM`,
`N` (pep8-naming). Excepciones notables: se ignora `E501` (lo gestiona el
formateador), `B008` (FastAPI usa *callables* en *defaults*: `Depends`/`Query`) y
`N803`/`N806` (se permiten nombres de dominio en español). `app/models.py` ignora
`N815` por espejar columnas de la BD.

---

## 11. Cómo extender el sistema

### 11.1 Añadir una fuente

Las fuentes se administran en la tabla `fuentes` y vía la API (rol editor/admin).

1. **Vía API** (recomendado): `POST /api/v1/fuentes` con el cuerpo `FuenteCreate`
   (`nombre`, `tipo`, `url`, `rss_url`, `alcance`, `credibilidad`, `verificada`,
   `estado`, …). Ver el esquema en [`schemas.py`](../backend/app/schemas.py) y la
   referencia en [API.md](API.md#10-fuentes).
2. **Vía SQL** (semilla/bootstrap): añada una fila al bloque `INSERT INTO fuentes`
   de [`seed.sql`](../database/seed.sql). Para que el ETL la ingiera debe tener
   `rss_url`, `estado = 'activa'` y `robots_ok = true`.
3. El ETL recoge automáticamente las fuentes `activa` en la próxima ejecución
   (`pipeline._load_fuentes()` → `rss_ingest.run(...)`).

### 11.2 Añadir un módulo al frontend

1. Registre la entrada de navegación en
   [`config.js`](../frontend/assets/js/config.js) (`VPID.nav`), con `view`, `label`
   e `icon`.
2. Implemente el renderizador `VPID.views.<view>(container)` en
   [`views.js`](../frontend/assets/js/views.js) (el router por hash lo invoca).
3. Si necesita datos nuevos, añada un método en
   [`api.js`](../frontend/assets/js/api.js) usando `withFallback('/ruta', () => …)`
   para conservar el fallback de demostración.
4. Para gráficos o mapas, reutilice los helpers de `charts.js` / `maps.js`.

### 11.3 Añadir un endpoint a la API

1. Cree o edite un módulo en
   [`app/api/routes/`](../backend/app/api/routes/) con su `APIRouter`.
2. Móntelo en [`app/api/router.py`](../backend/app/api/router.py) con su `prefix` y
   `tags`.
3. Proteja escrituras con `Depends(security.require_role("editor"))` (o el rol que
   corresponda) y registre acciones sensibles con `audit.log(...)`.
4. Para lecturas costosas y frecuentes, decore con `@cache.cached(ttl=..., key=...)`.
5. Documente el endpoint en [API.md](API.md).

### 11.4 Añadir una sección al Informe Ejecutivo

1. En [`pdf_report.py`](../backend/app/services/pdf_report.py), dentro de
   `build_pdf(...)`, añada un `Paragraph(...)` de título (estilo `h2`) y el contenido
   (tabla con `Table`/`TableStyle`, lista de `Paragraph`, o una imagen con `Image`).
2. Si la sección consume datos nuevos, añada un parámetro opcional a `build_pdf`
   (con *fallback* a `demo_data`) y aliméntelo desde `generate_and_store(...)`.
3. Verifique que la sección respeta la cabecera/pie y que el resultado sigue siendo
   un único PDF (recuerde: **PDF es el único formato de exportación**).

### 11.5 Ajustar reglas de alertas

Modifique `DEFAULT_RULES` en
[`alerts_engine.py`](../backend/app/services/alerts_engine.py) o pase un `rules`
personalizado a `evaluate(metrics, rules)`. Las claves son
`pico_menciones_pct`, `caida_sentimiento`, `narrativa_emergente_pct` y
`concentracion_territorial_pct`.

---

## 12. Resolución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `/health` muestra `db:false` | Postgres no accesible / `DATABASE_URL` mal. | Verifique credenciales y conectividad; en desarrollo la API sigue funcionando en DEMO. |
| `/health` muestra `cache:false` | Redis caído o `REDIS_URL` mal. | Es tolerable: la caché se desactiva sola. Revise Redis si necesita rendimiento. |
| El ETL no ingiere artículos | Fuentes sin `rss_url`, `estado != activa` o `robots_ok = false`. | Revise la tabla `fuentes`; recuerde `ETL_RESPECT_ROBOTS_TXT`. |
| Login falla en producción | `APP_ENV=production` exige usuario real. | Cree el usuario en `usuarios` o use el admin del seed (y cambie la clave). |
| CORS bloquea el frontend | `FRONTEND_ORIGIN` no coincide con el origen real. | Ajuste `FRONTEND_ORIGIN` (admite lista separada por comas). |
| El sentimiento siempre es léxico | `AI_PROVIDER=anthropic` sin `ANTHROPIC_API_KEY`. | Configure la clave; si no, se usa el léxico local por diseño. |
| Respuestas lentas | Falta caché o consultas pesadas. | Active Redis; revise la cabecera `X-Process-Time` (el backend loguea peticiones > 1000 ms). |

---

## 13. Documentos relacionados

- [ARQUITECTURA.md](ARQUITECTURA.md) — componentes, flujo de datos, modelo de datos.
- [API.md](API.md) — referencia completa de la API REST.
- [MANUAL_USUARIO.md](MANUAL_USUARIO.md) — guía de uso de los 12 módulos.
- [DESPLIEGUE.md](DESPLIEGUE.md) — despliegue local y producción.
- [USO_ETICO.md](USO_ETICO.md) — política de uso ético y legal.
