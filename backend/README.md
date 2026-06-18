# VPID — Backend (FastAPI)

API y motor de análisis del **Venezuela Political Intelligence Dashboard**.
Procesa exclusivamente **información pública** (medios, RSS, comunicados, APIs
autorizadas). **PDF es el único formato de exportación.**

## Stack
FastAPI · SQLAlchemy 2.0 async + asyncpg · Pydantic v2 · JWT (python-jose/passlib)
· Redis (caché) · APScheduler (ETL) · httpx + feedparser (ingesta) · reportlab +
matplotlib (PDF).

## Características clave
- **Degradación elegante**: si la base de datos o Redis no están disponibles, los
  endpoints de lectura responden con un *dataset de demostración* (`app/core/demo_data.py`).
  Así la API siempre es explorable. En `APP_ENV=production` se exige autenticación real.
- **RBAC** jerárquico: `lector < editor < analista < admin`.
- **ETL automático** diario: `ingest → clean → classify → analyze → aggregate` + informe PDF.

## Estructura
```
app/
  main.py            # App FastAPI, middleware, /health
  config.py          # Settings (.env)
  database.py        # Engine/sesiones async (lazy, no rompe el arranque)
  models.py          # ORM SQLAlchemy (espeja database/schema.sql)
  schemas.py         # Modelos Pydantic
  core/              # security, cache, audit, demo_data
  api/router.py      # Monta /api/v1
  api/routes/        # auth, dashboard, news, trends, narratives, sentiment,
                     # actors, territorial, alerts, sources, reports, search, etl
  services/          # sentiment, narratives, trends, alerts_engine, pdf_report
  etl/               # rss_ingest, clean, classify, analyze, aggregate,
                     # pipeline, scheduler
tests/               # pytest (corren sin DB/Redis gracias a demo mode)
```

## Ejecutar
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env        # ajustar valores

# API
uvicorn app.main:app --reload --port 8000
#   Docs:    http://localhost:8000/api/docs
#   Health:  http://localhost:8000/health

# ETL (worker programado)
python -m app.etl.scheduler          # demonio APScheduler
python -m app.etl.scheduler --once   # ejecuta pipeline + informe una vez
```

## Pruebas
```bash
pytest -q            # no requiere base de datos ni Redis
```

## Notas de seguridad
- Configure `JWT_SECRET_KEY` y credenciales fuertes en `.env` (nunca en el código).
- En producción (`APP_ENV=production`) se desactivan los *fallbacks* de demo y se
  exigen JWT y roles.
- Consulte `docs/USO_ETICO.md` para el uso responsable de fuentes abiertas.
