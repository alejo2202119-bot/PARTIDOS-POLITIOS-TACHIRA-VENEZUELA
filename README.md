<div align="center">

# 🛰️ Venezuela Political Intelligence Dashboard (VPID)

**Plataforma OSINT para el monitoreo y análisis de _información pública_** sobre actores,
organizaciones, partidos, líderes, medios, portales, comunicados, tendencias y narrativas
políticas de Venezuela.

_Inspirada en Bloomberg Terminal · Power BI · Tableau — con modo oscuro/claro, KPIs,
gráficos dinámicos, mapas interactivos e informes ejecutivos en PDF._

`HTML5` · `Tailwind CSS` · `ApexCharts` · `Chart.js` · `Leaflet` · `FastAPI` · `Node` · `PostgreSQL` · `Supabase` · `Redis`

</div>

> [!IMPORTANT]
> **Uso responsable.** VPID procesa **exclusivamente información pública y abiertamente
> disponible** (medios publicados, RSS, comunicados oficiales y APIs públicas autorizadas),
> con fines legítimos: periodismo, investigación académica, observación electoral y análisis
> de sociedad civil. **No** debe emplearse para vigilancia de personas privadas,
> desanonimización, rastreo de ubicación de personas, ni acoso o persecución política.
> Consulte la [Política de Uso Ético y Legal](docs/USO_ETICO.md).

---

## ✨ Características

- **12 módulos analíticos**: Dashboard Ejecutivo · Monitoreo de Noticias · Análisis de
  Tendencias · Detección de Narrativas · Análisis de Sentimiento (IA) · Ranking de Actores ·
  Monitoreo Territorial · Mapas Interactivos · Alertas Tempranas · Comparativos Históricos ·
  Centro de Inteligencia Digital · Informes Ejecutivos.
- **Interfaz premium y responsive** (escritorio/tablet/móvil) con **modo oscuro y claro**,
  buscador inteligente (⌘K), filtros avanzados, tarjetas KPI y gráficos dinámicos.
- **Clasificación multidimensional**: por fecha, estado, municipio, organización, actor,
  medio, tema, relevancia y sentimiento.
- **Detección de patrones**: crecimiento de menciones, evolución temporal, temas emergentes,
  alcance estimado y correlaciones entre eventos.
- **ETL automático diario** sin intervención manual: `ingest → clean → classify → analyze →
  aggregate → report`.
- **Informe Ejecutivo PDF** generado automáticamente cada día (portada institucional, KPIs,
  tendencias, actores, narrativas, análisis territorial, alertas, conclusiones y
  recomendaciones por IA). **PDF es el único formato de exportación.**
- **Producción**: autenticación JWT, control de roles (RBAC), auditoría, caché inteligente,
  monitoreo de rendimiento y arquitectura escalable.
- **Tabla `fuentes`** para administrar medios, organizaciones y fuentes abiertas verificables.

## 🧱 Arquitectura

```
┌───────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (HTML/Tailwind/JS · ApexCharts · Chart.js · Leaflet)             │
│  12 módulos · modo oscuro/claro · responsive · informe PDF (print)        │
└───────────────▲───────────────────────────────────────────────────────────┘
                │  REST /api/v1  (JWT)
┌───────────────┴───────────────────────────────────────────────────────────┐
│  BACKEND · FastAPI    auth · dashboard · noticias · tendencias · narrativas │
│                       sentimiento · actores · territorial · alertas ·       │
│                       fuentes · reportes(PDF) · búsqueda · etl              │
│  Servicios: sentimiento(IA/léxico) · narrativas · alertas · PDF(reportlab)  │
└──────▲────────────────────────▲───────────────────────────▲────────────────┘
       │                        │                           │
┌──────┴───────┐      ┌─────────┴─────────┐       ┌─────────┴──────────┐
│ PostgreSQL/  │      │   Redis (caché)   │       │  ETL (APScheduler) │
│  Supabase    │      └───────────────────┘       │ ingest→…→aggregate │
└──────────────┘                                  └────────────────────┘
```

Detalles en **[docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)**.

## 📁 Estructura del proyecto

```
.
├── frontend/              # SPA: index.html + assets/{css,js,img}
│   └── assets/js/         # config, mock, api, theme, charts, maps, views, app
├── backend/              # FastAPI: app/{api,core,services,etl,models,...} + tests
├── database/             # schema.sql · seed.sql · migrations/
├── deploy/               # nginx.conf (sirve frontend y proxya /api)
├── docs/                 # ARQUITECTURA · MANUAL_TECNICO · MANUAL_USUARIO · API · DESPLIEGUE · USO_ETICO
├── storage/reports/      # PDFs generados (archivo histórico)
├── docker-compose.yml    # db · redis · backend · etl · frontend
└── .env.example          # configuración (copiar a .env)
```

## 🚀 Puesta en marcha rápida

### Opción A — Docker Compose (todo el stack)
```bash
cp .env.example .env          # ajuste credenciales/secretos
docker compose up -d          # db, redis, backend (8000), etl, frontend (8080)
# Frontend:  http://localhost:8080
# API docs:  http://localhost:8000/api/docs
# Health:    http://localhost:8000/health
```

### Opción B — Desarrollo local
```bash
# 1) Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2) ETL (opcional)
python -m app.etl.scheduler --once      # ejecuta el pipeline + informe una vez

# 3) Frontend — abra frontend/index.html o sírvalo:
cd ../frontend && python -m http.server 5173
```

> [!TIP]
> **Modo demostración:** el frontend funciona **sin backend** (usa datos de muestra incluidos),
> y el backend responde con datos representativos si la base de datos/Redis no están
> disponibles (`APP_ENV != production`). Así puede explorar la plataforma de inmediato.
> Credenciales demo: cualquier usuario/clave inicia sesión.

## 🗄️ Base de datos

```bash
psql "$DATABASE_URL" -f database/schema.sql   # esquema (tablas, enums, vistas, índices)
psql "$DATABASE_URL" -f database/seed.sql     # geografía VE/Táchira, partidos, medios, temas
```
Modelo de datos completo en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md#5-modelo-de-datos).
Incluye la tabla **`fuentes`** (administración de medios/portales/RSS/comunicados) requerida.

## 🔌 API

Base `/api/v1` · documentación interactiva en `/api/docs` (Swagger) y `/api/redoc`.
Autenticación **JWT Bearer**; roles **lector < editor < analista < admin**.
Referencia completa en **[docs/API.md](docs/API.md)**.

| Grupo | Endpoints destacados |
|-------|----------------------|
| Auth | `POST /auth/login` · `GET /auth/me` |
| Dashboard | `GET /dashboard/kpis` · `GET /dashboard/overview` |
| Noticias | `GET /articulos` (filtros) |
| Tendencias | `GET /tendencias` · `GET /tendencias/emergentes` |
| Narrativas | `GET /narrativas` |
| Sentimiento | `GET /sentimiento/resumen` · `POST /sentimiento/analizar` |
| Actores | `GET /actores/ranking` |
| Territorial | `GET /territorial/resumen` |
| Alertas | `GET /alertas` · `POST /alertas/{id}/reconocer` |
| Fuentes | `GET/POST/PUT/DELETE /fuentes` |
| Reportes | `GET /reportes` · `POST /reportes/generar` · `GET /reportes/{id}/pdf` |

## 🧪 Pruebas

```bash
cd backend && pytest -q          # corre sin base de datos ni Redis (modo demo)
```

## 📚 Documentación

| Documento | Contenido |
|-----------|-----------|
| [ARQUITECTURA.md](docs/ARQUITECTURA.md) | Arquitectura, flujo de datos, modelo, seguridad, escalabilidad |
| [MANUAL_TECNICO.md](docs/MANUAL_TECNICO.md) | Instalación, configuración, ETL, servicios, extensión |
| [MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md) | Guía de uso de los 12 módulos, filtros, informes |
| [API.md](docs/API.md) | Referencia REST completa con ejemplos |
| [DESPLIEGUE.md](docs/DESPLIEGUE.md) | Despliegue local, Supabase y producción |
| [USO_ETICO.md](docs/USO_ETICO.md) | Política de uso ético y legal |

## 🛡️ Seguridad y privacidad

- Procesamiento de **información pública** únicamente.
- JWT + RBAC + auditoría (`auditoria`) + RLS en Supabase.
- Secretos fuera del código (`.env`); en `APP_ENV=production` se exigen autenticación y roles.
- Exportación **solo en PDF** (sin Excel/CSV/Word), almacenada para consulta histórica.

## 📄 Licencia

[MIT](LICENSE) con adenda de uso ético. El cumplimiento legal y el uso responsable son
responsabilidad del usuario.
