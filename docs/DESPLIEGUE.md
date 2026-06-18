# Guía de Despliegue — Venezuela Political Intelligence Dashboard (VPID)

> **Alcance del sistema:** VPID procesa **únicamente información pública** (medios, RSS,
> comunicados oficiales y APIs públicas autorizadas). Consulte la
> [Política de Uso Ético y Legal](USO_ETICO.md) y la [Arquitectura](ARQUITECTURA.md).

Esta guía cubre el despliegue de VPID en local/staging (con Docker Compose) y en
producción (Postgres gestionado/Supabase, backend con workers, worker ETL, frontend en
CDN/nginx con HTTPS). Para instalación de desarrollo paso a paso, ver
[MANUAL_TECNICO.md](MANUAL_TECNICO.md#4-instalación-paso-a-paso).

## Tabla de contenidos

1. [Prerrequisitos](#1-prerrequisitos)
2. [Puesta en marcha rápida (Docker Compose)](#2-puesta-en-marcha-rápida-docker-compose)
3. [Variables de entorno y secretos](#3-variables-de-entorno-y-secretos)
4. [Provisión de base de datos](#4-provisión-de-base-de-datos)
5. [Provisión en Supabase](#5-provisión-en-supabase)
6. [Despliegue en producción](#6-despliegue-en-producción)
7. [HTTPS y reverse proxy](#7-https-y-reverse-proxy)
8. [Copias de seguridad](#8-copias-de-seguridad)
9. [Monitoreo y observabilidad](#9-monitoreo-y-observabilidad)
10. [Escalado](#10-escalado)
11. [Lista de verificación de endurecimiento de seguridad](#11-lista-de-verificación-de-endurecimiento-de-seguridad)
12. [Documentos relacionados](#12-documentos-relacionados)

---

## 1. Prerrequisitos

| Requisito | Versión | Uso |
|-----------|---------|-----|
| Docker + Docker Compose | reciente | Stack local/staging. |
| Python | 3.11+ | Backend y ETL en despliegues sin contenedor. |
| PostgreSQL | 15+ (o Supabase) | Base de datos (extensiones `pgcrypto`, `pg_trgm`, `unaccent`, `citext`). |
| Redis | 7+ | Caché (opcional pero recomendado). |
| nginx | 1.27+ | Estáticos + *reverse proxy* a `/api/`. |
| Certificado TLS | — | HTTPS en producción (Let's Encrypt u otro). |

> El backend arranca incluso sin BD ni Redis gracias al
> [modo DEMO](MANUAL_TECNICO.md#6-el-modo-demo-degradación-elegante). En **producción**
> (`APP_ENV=production`) se exige BD real y autenticación; configure todo antes.

---

## 2. Puesta en marcha rápida (Docker Compose)

El stack local/staging está descrito en
[`docker-compose.yml`](../docker-compose.yml). Levanta cinco servicios.

```bash
git clone <repo-url> PARTIDOS-POLITIOS-TACHIRA-VENEZUELA
cd PARTIDOS-POLITIOS-TACHIRA-VENEZUELA

# IMPRESCINDIBLE: docker-compose usa env_file: .env en backend y etl
cp .env.example .env
#   Edite .env: contraseñas, JWT_SECRET_KEY, FRONTEND_ORIGIN, etc. (ver §3)

docker compose up -d --build
docker compose ps
docker compose logs -f backend       # seguir logs del API
```

| Servicio | Qué levanta | Detalle |
|----------|-------------|---------|
| **db** | `postgres:15-alpine` (puerto 5432) | Monta `database/schema.sql` y `database/seed.sql` en `/docker-entrypoint-initdb.d/`, por lo que **inicializa el esquema y la semilla automáticamente** en el primer arranque (volumen vacío). *Healthcheck* con `pg_isready`. |
| **redis** | `redis:7-alpine` (puerto 6379) | Caché con persistencia AOF (`--appendonly yes`). |
| **backend** | build `./backend` (puerto 8000) | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`. Depende de `db` *healthy* y `redis`. Monta `./storage`. |
| **etl** | build `./backend` | `python -m app.etl.scheduler` (demonio APScheduler: pipeline 05:00 + informe 06:00). Monta `./storage`. |
| **frontend** | `nginx:1.27-alpine` (puerto 8080) | Sirve `frontend/` y aplica [`deploy/nginx.conf`](../deploy/nginx.conf) (proxy `/api/` → `backend:8000`). |

Acceda a:

- **App:** `http://localhost:8080`
- **API / Swagger:** `http://localhost:8080/api/docs`
- **Health:** `http://localhost:8000/health` (puerto directo del backend)

Comandos útiles:

```bash
docker compose down                  # detener
docker compose down -v               # detener y BORRAR volúmenes (datos)
docker compose exec etl python -m app.etl.scheduler --once   # forzar un ciclo ETL+informe
docker compose exec db psql -U vpid_app -d vpid -c "select count(*) from articulos;"
```

> **Nota:** la inicialización automática de `schema.sql`/`seed.sql` solo ocurre cuando
> el volumen de datos de Postgres está **vacío**. Para reaplicarla, recree el volumen
> (`docker compose down -v`).

---

## 3. Variables de entorno y secretos

Todas las claves se documentan en
[MANUAL_TECNICO.md §5](MANUAL_TECNICO.md#5-configuración-todas-las-claves-de-env). Para
producción, preste especial atención a:

| Clave | Recomendación en producción |
|-------|------------------------------|
| `APP_ENV` | `production` (desactiva el modo DEMO y exige JWT/roles). |
| `APP_DEBUG` | `false`. |
| `JWT_SECRET_KEY` | Secreto aleatorio de **64+ caracteres** (ver abajo). |
| `POSTGRES_PASSWORD` / `DATABASE_URL` | Credenciales fuertes; `DATABASE_URL` tiene prioridad. |
| `FRONTEND_ORIGIN` | Dominio(s) reales del frontend (lista separada por comas), p. ej. `https://vpid.example.org`. |
| `REDIS_URL` | URL del Redis gestionado/privado. |
| `SUPABASE_SERVICE_ROLE_KEY` | **Secreto** — solo en el backend, nunca en el frontend. |
| `ANTHROPIC_API_KEY` | Solo si `AI_PROVIDER=anthropic`. |
| `REPORTS_STORAGE_PATH` | Ruta persistente para los PDFs (volumen/disco montado). |

Genere un secreto JWT fuerte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Gestión de secretos:** no comprometa `.env` en el repositorio (ya está en
`.gitignore`). En producción use el gestor de secretos de su plataforma (variables de
entorno del orquestador, Docker/Swarm secrets, Kubernetes Secrets, Vault, etc.) en
lugar de un archivo `.env` plano.

---

## 4. Provisión de base de datos

Para Postgres gestionado (no el contenedor de Compose), aplique el esquema y la semilla
en orden:

```bash
export DATABASE_URL="postgresql://usuario:clave@host:5432/vpid"   # forma psql estándar

psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/seed.sql
```

> El backend usa la URL **async** (`postgresql+asyncpg://...`) en `DATABASE_URL`; para
> el cliente `psql` use la forma `postgresql://...`.

El esquema crea extensiones (`pgcrypto`, `pg_trgm`, `unaccent`, `citext`), tipos ENUM,
tablas, índices (incluido el GIN full-text en español sobre `articulos.tsv`) y las
vistas `v_ranking_actores` y `v_resumen_territorial`. La semilla carga roles, el admin
por defecto (`admin@vpid.local` / `ChangeMe!2026` — **cámbiela**), 24 estados, 29
municipios de Táchira, organizaciones y figuras públicas de referencia, fuentes
verificables, temas y un conjunto **sintético** de datos de demostración.

Con un *runner* de migraciones, use el puntero
[`database/migrations/0001_initial.sql`](../database/migrations/0001_initial.sql)
(ejecuta `schema.sql` y `seed.sql`). Las migraciones siguientes deben contener solo
`ALTER` incrementales.

---

## 5. Provisión en Supabase

1. **Crear el proyecto** en Supabase y obtener `SUPABASE_URL`, `SUPABASE_ANON_KEY` y
   `SUPABASE_SERVICE_ROLE_KEY` (esta última es secreta).
2. **Aplicar el esquema y la semilla:** desde el *SQL Editor* o `psql`, ejecute
   `database/schema.sql` y luego `database/seed.sql`. Supabase incluye la extensión
   `citext`. (`pgcrypto`, `pg_trgm` y `unaccent` se crean con `CREATE EXTENSION IF NOT
   EXISTS` en el propio esquema.)
3. **Habilitar Row-Level Security (RLS):** active RLS por tabla y defina políticas por
   rol. El esquema incluye un ejemplo comentado para `reportes`:

   ```sql
   ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;
   CREATE POLICY reportes_read ON reportes FOR SELECT
     USING ( auth.role() IN ('admin','analista','editor','lector') );
   ```

   Replique el patrón en las tablas que exponga directamente a clientes Supabase y
   mantenga las políticas en `database/migrations`.
4. **Configurar Auth:** si delega la identidad en Supabase Auth, enlace cada cuenta vía
   `usuarios.supabase_uid` (el campo `password_hash` puede quedar nulo cuando la
   verificación la realiza Supabase). Vea el modelo de seguridad en
   [ARQUITECTURA.md §6](ARQUITECTURA.md#6-modelo-de-seguridad).
5. **Apuntar el backend** a Supabase con `DATABASE_URL`
   (`postgresql+asyncpg://...supabase...`) y las claves anteriores en `.env`/secretos.

---

## 6. Despliegue en producción

Arquitectura recomendada: **Postgres gestionado** (o Supabase) + **Redis gestionado** +
**backend** (varios workers) + **worker ETL** independiente + **frontend** estático en
CDN/nginx tras HTTPS.

### 6.1 Backend (uvicorn / gunicorn con workers)

La API no tiene estado; escálela horizontalmente con varios workers detrás de nginx.

```bash
cd backend
pip install -r requirements.txt

# Opción A — uvicorn con varios workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers

# Opción B — gunicorn gestionando workers uvicorn (recomendado en producción)
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 --bind 0.0.0.0:8000 \
  --timeout 60 --graceful-timeout 30 --max-requests 1000 --max-requests-jitter 100
```

Regla orientativa: `workers ≈ 2 × núcleos + 1`. Ejecute con `APP_ENV=production` y
`APP_DEBUG=false`. Asegure conectividad a `DATABASE_URL` y `REDIS_URL`.

> El contenedor de backend de Compose ya arranca con `--workers 2`; para producción se
> recomienda subir el número o usar gunicorn según la carga.

### 6.2 Worker ETL

El ETL debe correr como **proceso/servicio aparte** del API (no en el mismo proceso).
Dos estrategias:

```bash
# A) Demonio APScheduler (se programa solo: pipeline 05:00 + informe 06:00 VET)
python -m app.etl.scheduler

# B) Ejecución única disparada por el cron del sistema / del orquestador
python -m app.etl.scheduler --once
```

Para la opción B, un ejemplo de crontab del sistema (ajuste la zona horaria del host a
`America/Caracas` o use `CRON_TZ`):

```cron
CRON_TZ=America/Caracas
0 5 * * *  cd /app/backend && /app/backend/.venv/bin/python -m app.etl.scheduler --once
```

> Ejecute **una sola** instancia del worker ETL para evitar ingestas duplicadas. El
> worker necesita la misma configuración (`.env`/secretos) y acceso de escritura a
> `REPORTS_STORAGE_PATH`.

### 6.3 Frontend (CDN / nginx)

El frontend es **estático** (sin *build*). Sírvalo desde un CDN o desde nginx usando
[`deploy/nginx.conf`](../deploy/nginx.conf), que ya:

- sirve los estáticos de `frontend/` con `try_files` (fallback SPA a `index.html`);
- cachea `/assets/` 7 días (`Cache-Control: public, max-age=604800`);
- aplica GZip;
- añade cabeceras de seguridad (`X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy`);
- **proxya `/api/` → `backend:8000`** (reenvía `Host`, `X-Real-IP`,
  `X-Forwarded-For`, `X-Forwarded-Proto`).

Si el backend está en otro host, ajuste el `proxy_pass` del bloque `location /api/`.
Cuando sirva el frontend desde un CDN/dominio distinto al de la API, configure
`FRONTEND_ORIGIN` en consecuencia para el CORS.

---

## 7. HTTPS y reverse proxy

Sirva **siempre por HTTPS** en producción. Termine TLS en nginx (o en el balanceador) y
mantenga el proxy a la API. Esquema de bloque TLS (complementa `deploy/nginx.conf`):

```nginx
server {
    listen 443 ssl http2;
    server_name vpid.example.org;

    ssl_certificate     /etc/letsencrypt/live/vpid.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vpid.example.org/privkey.pem;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    root /usr/share/nginx/html;
    index index.html;

    location /assets/ { expires 7d; add_header Cache-Control "public, max-age=604800"; }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    location / { try_files $uri $uri/ /index.html; }
}

# Redirección 80 → 443
server { listen 80; server_name vpid.example.org; return 301 https://$host$request_uri; }
```

Arranque uvicorn/gunicorn con `--proxy-headers` para que respete `X-Forwarded-*`.
Certificados con Let's Encrypt (`certbot`) o el emisor de su preferencia.

---

## 8. Copias de seguridad

| Qué respaldar | Cómo | Frecuencia sugerida |
|---------------|------|---------------------|
| **Base de datos** | `pg_dump` (o backups gestionados de Supabase / proveedor). | Diaria + retención. |
| **Informes PDF** | Copia de `REPORTS_STORAGE_PATH` (`storage/reports/`). | Diaria. |
| **Configuración/secretos** | Respaldo seguro de `.env`/secretos (cifrado, fuera del repo). | En cada cambio. |

```bash
# Volcado lógico de la base
pg_dump "postgresql://usuario:clave@host:5432/vpid" -Fc -f vpid_$(date +%F).dump

# Restauración
pg_restore -d "postgresql://usuario:clave@host:5432/vpid" --clean vpid_2026-06-18.dump
```

> La integridad de cada informe se puede verificar con su `pdf_sha256` registrado en la
> tabla `reportes`.

---

## 9. Monitoreo y observabilidad

| Señal | Dónde | Qué indica |
|-------|-------|------------|
| **`GET /health`** | Endpoint del backend | `status`, `version`, `db`, `cache`, `demo_mode`, `uptime_s` y `extra` (env, proveedor IA). Úselo como *liveness/readiness probe*. |
| **`etl_ejecuciones`** | Tabla de la BD | Histórico de ejecuciones del pipeline (job, estado, items, duración). |
| **`GET /api/v1/etl/estado`** | Endpoint | Últimas corridas y próximo ciclo programado. |
| **`auditoria`** | Tabla de la BD | Bitácora *append-only* de acciones sensibles (login, generación de informes, cambios en fuentes). |
| **`X-Process-Time`** | Cabecera de respuesta | Duración de cada solicitud en ms. El backend loguea como *warning* las peticiones > 1000 ms. |
| **Logs de aplicación** | `stdout` de backend/etl | Formato `fecha nivel logger — mensaje`. Centralícelos (ELK, Loki, CloudWatch…). |

Ejemplos de chequeo:

```bash
curl -fsS https://vpid.example.org/api/v1/../../health   # /health del backend
docker compose exec db psql -U vpid_app -d vpid \
  -c "select job, estado, items_out, duracion_ms, iniciado_en from etl_ejecuciones order by iniciado_en desc limit 10;"
```

Configure alertas externas sobre: `/health` no `ok`, `db:false` en producción,
ausencia de ejecuciones ETL recientes y ausencia del informe diario.

---

## 10. Escalado

- **API:** sin estado → añada réplicas/workers detrás de nginx o un balanceador. La
  caché Redis reduce la carga de la BD; el sistema degrada a consultar la BD si Redis
  cae.
- **ETL:** desacoplado del API. Mantenga **una** instancia para la cadencia diaria; si
  el volumen crece, particione por fuentes o migre a una cola distribuida (Celery) como
  se anticipa en [ARQUITECTURA.md §9](ARQUITECTURA.md#9-decisiones-tecnológicas-y-compromisos).
- **Base de datos:** use réplicas de lectura para descargar consultas analíticas;
  aproveche las agregaciones precomputadas (`tendencias`, `kpi_snapshots`) y los índices
  GIN/B-tree existentes.
- **Caché:** ajuste `CACHE_TTL_SECONDS` (300 s por defecto). Como los KPIs/tendencias se
  recomputan a diario, un TTL de minutos da respuestas casi instantáneas sin datos
  obsoletos relevantes.
- **Frontend:** servir `/assets/` desde CDN con caché de larga duración.
- **Ingesta:** controle la presión con `ETL_MAX_ARTICLES_PER_SOURCE` y `frecuencia_min`
  por fuente.

---

## 11. Lista de verificación de endurecimiento de seguridad

- [ ] `APP_ENV=production` y `APP_DEBUG=false` (desactiva fallbacks de demo; exige JWT/roles).
- [ ] `JWT_SECRET_KEY` aleatorio de 64+ caracteres, fuera del repositorio.
- [ ] Contraseñas fuertes en `POSTGRES_PASSWORD` / `DATABASE_URL`.
- [ ] **Cambiada** la contraseña del admin del seed (`admin@vpid.local`) en el primer acceso.
- [ ] `FRONTEND_ORIGIN` restringido a los dominios reales (CORS).
- [ ] Secretos servidos por un gestor de secretos; `.env` nunca versionado.
- [ ] `SUPABASE_SERVICE_ROLE_KEY` y claves de IA **solo** en el backend, nunca en el frontend.
- [ ] **HTTPS** obligatorio; redirección 80 → 443; HSTS activado.
- [ ] Cabeceras de seguridad de nginx presentes (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).
- [ ] **RLS habilitado** y políticas por rol definidas en despliegues Supabase.
- [ ] Puertos de BD/Redis **no** expuestos a Internet (red privada; sin publicar 5432/6379).
- [ ] uvicorn/gunicorn con `--proxy-headers` tras el reverse proxy.
- [ ] ETL respeta `robots.txt`/ToS (`ETL_RESPECT_ROBOTS_TXT=true`) y usa un `ETL_USER_AGENT` identificado.
- [ ] Copias de seguridad de BD y de `storage/reports/` verificadas y probadas (restauración).
- [ ] Auditoría (`auditoria`) activa y revisada periódicamente (solo admin).
- [ ] Monitoreo de `/health`, `etl_ejecuciones` y del informe diario con alertas.
- [ ] Una única instancia del worker ETL (evita ingestas duplicadas).
- [ ] Uso conforme a la [Política de Uso Ético](USO_ETICO.md): solo información pública; nada de vigilancia de personas privadas.

---

## 12. Documentos relacionados

- [ARQUITECTURA.md](ARQUITECTURA.md) — componentes, seguridad, caché y escalabilidad.
- [MANUAL_TECNICO.md](MANUAL_TECNICO.md) — instalación, configuración y motores.
- [API.md](API.md) — referencia de la API REST.
- [MANUAL_USUARIO.md](MANUAL_USUARIO.md) — guía de uso de los 12 módulos.
- [USO_ETICO.md](USO_ETICO.md) — política de uso ético y legal.
