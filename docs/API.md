# Referencia de la API REST — Venezuela Political Intelligence Dashboard (VPID)

> **Alcance:** la API expone, sobre **información pública** (OSINT), los datos de los 12
> módulos de VPID. Consulte la [Política de Uso Ético y Legal](USO_ETICO.md) y la
> [Arquitectura](ARQUITECTURA.md).

Esta es la referencia del contrato REST. El servidor genera además documentación
interactiva: **Swagger UI** en [`/api/docs`](/api/docs), **ReDoc** en
[`/api/redoc`](/api/redoc) y el esquema OpenAPI en `/api/openapi.json`.

## Tabla de contenidos

1. [Información general](#1-información-general)
2. [Autenticación (Bearer JWT)](#2-autenticación-bearer-jwt)
3. [Formato de error](#3-formato-de-error)
4. [Paginación](#4-paginación)
5. [Endpoints del sistema](#5-endpoints-del-sistema)
6. [Auth](#6-auth)
7. [Dashboard](#7-dashboard)
8. [Noticias](#8-noticias)
9. [Tendencias](#9-tendencias)
10. [Narrativas](#10-narrativas)
11. [Sentimiento](#11-sentimiento)
12. [Actores](#12-actores)
13. [Territorial](#13-territorial)
14. [Alertas](#14-alertas)
15. [Fuentes](#15-fuentes)
16. [Reportes](#16-reportes)
17. [Búsqueda](#17-búsqueda)
18. [ETL](#18-etl)
19. [Comparativos](#19-comparativos)
20. [Matriz de roles (RBAC)](#20-matriz-de-roles-rbac)
21. [Documentos relacionados](#21-documentos-relacionados)

---

## 1. Información general

| Aspecto | Valor |
|---------|-------|
| **URL base** | `/api/v1` |
| **Formato** | JSON (UTF-8). Las descargas de informe devuelven `application/pdf`. |
| **Documentación interactiva** | `/api/docs` (Swagger), `/api/redoc` (ReDoc) |
| **Esquema OpenAPI** | `/api/openapi.json` |
| **Salud** | `/health` (fuera del prefijo `/api/v1`) |
| **Compresión** | GZip para respuestas ≥ 1024 bytes |
| **CORS** | Restringido a `FRONTEND_ORIGIN` |
| **Cabecera de tiempo** | Toda respuesta incluye `X-Process-Time` (ms) |

> **Única exportación: PDF.** La plataforma no expone exportación a Excel, CSV ni Word.

> **Modo DEMO:** cuando `APP_ENV` no es `production`, los endpoints de lectura responden
> con un dataset **representativo y sintético** si la base de datos está vacía o
> inaccesible, y la autenticación es permisiva. En producción se exigen JWT y roles
> reales. Detalles en [MANUAL_TECNICO.md §6](MANUAL_TECNICO.md#6-el-modo-demo-degradación-elegante).

---

## 2. Autenticación (Bearer JWT)

La autenticación es por **token JWT** en el encabezado `Authorization: Bearer <token>`.

**Flujo:** envíe credenciales a `POST /api/v1/auth/login` y use el `access_token`
devuelto en las siguientes solicitudes.

```bash
# 1) Login
curl -s -X POST https://host/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vpid.local","password":"ChangeMe!2026"}'
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "9f1c...e2",
    "email": "admin@vpid.local",
    "nombre": "Administrador VPID",
    "rol": "admin"
  }
}
```

```bash
# 2) Solicitud autenticada
curl -s https://host/api/v1/reportes \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiI..."
```

El token incluye el rol (`rol`) usado por el control de acceso (RBAC). El *access
token* expira según `ACCESS_TOKEN_EXPIRE_MINUTES` (30 min); renueve con
`POST /auth/refresh` usando el `refresh_token`.

---

## 3. Formato de error

Los errores siguen la convención de FastAPI: código HTTP + cuerpo con `detail`.

```json
{ "detail": "Credenciales inválidas" }
```

| Código | Significado | Ejemplo |
|--------|-------------|---------|
| `400` | Solicitud inválida | Parámetros mal formados. |
| `401` | No autenticado / token inválido | `{"detail":"No autenticado"}` |
| `403` | Permisos insuficientes (RBAC) | `{"detail":"Permisos insuficientes"}` |
| `404` | Recurso no encontrado | `{"detail":"Actor no encontrado"}` |
| `422` | Error de validación | Lista de errores por campo (Pydantic). |
| `500` | Error interno | `{"detail":"Error interno del servidor"}` |

---

## 4. Paginación

Las colecciones paginadas usan la envoltura estándar `Page`:

```json
{
  "items": [ /* ... */ ],
  "total": 60,
  "page": 1,
  "size": 50
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `items` | array | Elementos de la página actual. |
| `total` | int | Total de elementos que cumplen el filtro. |
| `page` | int | Página actual (1-based). |
| `size` | int | Tamaño de página. |

> Algunas colecciones de menor volumen (narrativas, alertas, actores, fuentes,
> territorial, reportes) devuelven `{ "items": [...] }` sin los campos de paginación.

---

## 5. Endpoints del sistema

Fuera del prefijo `/api/v1`:

### `GET /health`

Sonda de vida/disponibilidad con estado de la BD y la caché.

```json
{
  "status": "ok",
  "version": "1.0.0",
  "db": true,
  "cache": true,
  "demo_mode": false,
  "uptime_s": 8123.4,
  "extra": { "env": "production", "ai_provider": "local" }
}
```

### `GET /`

Metadatos básicos del servicio.

```json
{
  "name": "Venezuela Political Intelligence Dashboard",
  "version": "1.0.0",
  "docs": "/api/docs",
  "health": "/health",
  "note": "Procesa exclusivamente información pública. Exportación únicamente en PDF."
}
```

---

## 6. Auth

Prefijo: `/api/v1/auth`.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `POST` | `/auth/login` | Pública | Inicia sesión y devuelve tokens. |
| `POST` | `/auth/refresh` | Pública (con refresh token) | Renueva el *access token*. |
| `GET` | `/auth/me` | Bearer | Devuelve el usuario actual. |

### `POST /auth/login`

**Cuerpo** (`LoginRequest`): `{ "email": "...", "password": "..." }`
(el `email` admite identificador con dominio `.local`).

Respuesta: ver [§2](#2-autenticación-bearer-jwt) (`TokenResponse`).

### `POST /auth/refresh`

**Cuerpo** (`RefreshRequest`): `{ "refresh_token": "..." }`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer",
  "user": null
}
```

### `GET /auth/me`

```json
{ "id": "9f1c...e2", "email": "admin@vpid.local", "nombre": "Administrador VPID", "rol": "admin" }
```

---

## 7. Dashboard

Prefijo: `/api/v1/dashboard`. Módulo **Dashboard Ejecutivo**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/dashboard/kpis` | Bearer | Tarjetas KPI del día (cacheado). |
| `GET` | `/dashboard/overview` | Bearer | Resumen compacto: actores, narrativas, alertas, sentimiento. |

### `GET /dashboard/kpis`

```json
{
  "fecha": "2026-06-18",
  "total_articulos": 1248,
  "total_menciones": 3962,
  "fuentes_activas": 11,
  "sentimiento_global": -0.06,
  "narrativas_activas": 7,
  "narrativas_emergentes": 2,
  "alertas_abiertas": 3,
  "alcance_total": 18940000,
  "deltas": {
    "total_articulos": 12.4,
    "total_menciones": 18.1,
    "fuentes_activas": 0.0,
    "sentimiento_global": -8.2,
    "alcance_total": 9.7
  },
  "spark": {
    "total_articulos": [78, 85, 91, 88, 96, 102, 110],
    "total_menciones": [260, 275, 268, 290, 305, 298, 320],
    "alcance_total": [1100000, 1180000, 1240000, 1300000],
    "sentimiento_global": [-0.04, -0.06, -0.05, -0.07]
  }
}
```

### `GET /dashboard/overview`

```json
{
  "actores": [
    { "id": "a1", "nombre": "María Corina Machado", "cargo": "Líder político",
      "organizacion": "VV", "menciones": 480, "sentimiento_prom": 0.12,
      "alcance_estimado": 2400000 }
  ],
  "narrativas": [
    { "id": "n1", "titulo": "Llamado a la unidad opositora de cara al proceso electoral",
      "tema_id": "t1", "sentimiento": "neutral", "relevancia": "alta",
      "emergente": true, "total_articulos": 96, "alcance_estimado": 1800000 }
  ],
  "alertas": [
    { "id": "al1", "titulo": "Pico de menciones detectado", "severidad": "alta",
      "estado": "abierta" }
  ],
  "sentimiento": { "positivo": 28, "neutral": 41, "negativo": 31, "score_global": -0.06 }
}
```

---

## 8. Noticias

Prefijo: `/api/v1/articulos`. Módulo **Monitoreo de Noticias**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/articulos` | Bearer | Lista paginada y filtrable de artículos. |
| `GET` | `/articulos/{articulo_id}` | Bearer | Detalle de un artículo. |

### `GET /articulos`

**Parámetros de consulta:**

| Parámetro | Tipo | Por defecto | Descripción |
|-----------|------|-------------|-------------|
| `q` | string | — | Búsqueda en titular + actor + fuente. |
| `tema` | string | — | Filtra por tema. |
| `estado` | string | — | Filtra por estado (geográfico). |
| `relevancia` | string | — | `baja` \| `media` \| `alta` \| `critica`. |
| `sentimiento` | string | — | `positivo` \| `neutral` \| `negativo`. |
| `fuente` | string | — | Filtra por nombre de fuente. |
| `page` | int | `1` | Página (≥ 1). |
| `size` | int | `50` | Tamaño (1–200). |

```bash
curl -s "https://host/api/v1/articulos?tema=Elecciones&sentimiento=negativo&size=2" \
  -H "Authorization: Bearer <token>"
```

```json
{
  "items": [
    {
      "id": "art1",
      "titulo": "Dirigentes opositores presentan agenda regional en San Cristóbal",
      "resumen": "Resumen sintético de demostración para el panel de monitoreo de información pública.",
      "fuente": "Efecto Cocuyo", "fuente_id": "f4", "tipo_fuente": "portal",
      "tema": "Elecciones", "tema_color": "#6366f1",
      "estado": "Táchira", "actor": "María Corina Machado",
      "publicado_en": "2026-06-18T13:20:00",
      "relevancia": "alta", "sentimiento": "negativo", "score": -0.42,
      "alcance_estimado": 64000, "url": "#"
    }
  ],
  "total": 12, "page": 1, "size": 2
}
```

### `GET /articulos/{articulo_id}`

Devuelve el objeto artículo (igual forma que un elemento de `items`) o `404`.

---

## 9. Tendencias

Prefijo: `/api/v1/tendencias`. Módulo **Análisis de Tendencias**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/tendencias` | Bearer | Series diarias de menciones por tema. |
| `GET` | `/tendencias/emergentes` | Bearer | Temas emergentes por crecimiento reciente. |

### `GET /tendencias`

**Parámetros:** `desde`, `hasta`, `tema` (filtra una serie), `granularidad` (`dia`).

```json
{
  "series": [
    {
      "name": "Elecciones", "color": "#6366f1",
      "data": [ { "x": "2026-05-20", "y": 64 }, { "x": "2026-05-21", "y": 71 } ]
    }
  ],
  "emergentes": [
    { "tema": "Observación electoral", "crecimiento": 214, "menciones": 342 }
  ]
}
```

### `GET /tendencias/emergentes`

```json
[
  { "tema": "Observación electoral", "crecimiento": 214, "menciones": 342 },
  { "tema": "Servicios en la frontera", "crecimiento": 158, "menciones": 221 },
  { "tema": "Unidad opositora", "crecimiento": 96, "menciones": 588 }
]
```

---

## 10. Narrativas

Prefijo: `/api/v1/narrativas`. Módulo **Detección de Narrativas**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/narrativas` | Bearer | Lista de narrativas (filtrable). |
| `GET` | `/narrativas/{narrativa_id}` | Bearer | Detalle de una narrativa. |

### `GET /narrativas`

**Parámetros:** `emergente` (bool), `tema` (filtra por `tema_id`).

```json
{
  "items": [
    {
      "id": "n1",
      "titulo": "Llamado a la unidad opositora de cara al proceso electoral",
      "tema_id": "t1", "sentimiento": "neutral", "relevancia": "alta",
      "emergente": true, "total_articulos": 96, "alcance_estimado": 1800000,
      "variacion": 142.0,
      "palabras_clave": ["unidad", "elecciones", "región"],
      "serie": [ { "x": "2026-06-04", "y": 8 }, { "x": "2026-06-05", "y": 12 } ],
      "ultima_vista": "2026-06-18T09:00:00"
    }
  ]
}
```

### `GET /narrativas/{narrativa_id}`

Devuelve la narrativa o `404` (`{"detail":"Narrativa no encontrada"}`).

---

## 11. Sentimiento

Prefijo: `/api/v1/sentimiento`. Módulo **Análisis de Sentimiento (IA)**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/sentimiento/resumen` | Bearer | Distribución + score global + series por tema. |
| `GET` | `/sentimiento/series` | Bearer | Series temporales de sentimiento por tema. |
| `POST` | `/sentimiento/analizar` | Bearer | Puntúa un texto público arbitrario. |

### `GET /sentimiento/resumen`

```json
{
  "resumen": { "positivo": 28, "neutral": 41, "negativo": 31, "score_global": -0.06 },
  "series": [
    {
      "name": "Elecciones", "color": "#6366f1",
      "data": [ { "x": "2026-06-04", "y": -0.12 }, { "x": "2026-06-05", "y": 0.05 } ]
    }
  ]
}
```

### `GET /sentimiento/series`

```json
{
  "series": [
    { "name": "Derechos Humanos", "color": "#ef4444",
      "data": [ { "x": "2026-06-04", "y": -0.31 } ] }
  ]
}
```

### `POST /sentimiento/analizar`

**Cuerpo:** `{ "texto": "El acuerdo abre una oportunidad de diálogo y unidad." }`

```json
{
  "etiqueta": "positivo",
  "score": 0.667,
  "confianza": 0.62,
  "emociones": { "alegria": 0.33 },
  "modelo": "local-lexicon"
}
```

> El campo `modelo` refleja el proveedor configurado (`AI_PROVIDER`): `local-lexicon`
> o el modelo Anthropic (`ANTHROPIC_MODEL`) si está activo y con clave.

---

## 12. Actores

Prefijo: `/api/v1/actores`. Módulo **Ranking de Actores Públicos**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/actores/ranking` | Bearer | Actores ordenados por menciones. |
| `GET` | `/actores` | Bearer | Lista completa de actores. |
| `GET` | `/actores/{actor_id}` | Bearer | Detalle de un actor. |

### `GET /actores/ranking`

**Parámetros:** `desde`, `hasta`, `limit` (1–100, por defecto 20).

```json
{
  "items": [
    {
      "id": "a1", "nombre": "María Corina Machado", "cargo": "Líder político",
      "organizacion": "VV", "menciones": 480, "sentimiento_prom": 0.12,
      "alcance_estimado": 2400000,
      "trend": [22, 28, 31, 35, 40, 44, 49]
    }
  ]
}
```

### `GET /actores/{actor_id}`

Devuelve el actor o `404` (`{"detail":"Actor no encontrado"}`).

---

## 13. Territorial

Prefijo: `/api/v1/territorial`. Módulos **Monitoreo Territorial** y **Mapas Interactivos**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/territorial/resumen` | Bearer | Volumen y sentimiento medio por estado. |
| `GET` | `/territorial/estado/{estado_id}` | Bearer | Detalle de un estado. |

### `GET /territorial/resumen`

```json
{
  "items": [
    { "id": "e-tac", "estado": "Táchira", "latitud": 7.7669, "longitud": -72.225,
      "articulos": 312, "sentimiento_prom": -0.18 },
    { "id": "e-zul", "estado": "Zulia", "latitud": 10.6427, "longitud": -71.6125,
      "articulos": 240, "sentimiento_prom": -0.05 }
  ]
}
```

### `GET /territorial/estado/{estado_id}`

Devuelve el estado o `404` (`{"detail":"Estado no encontrado"}`).

---

## 14. Alertas

Prefijo: `/api/v1/alertas`. Módulo **Sistema de Alertas Tempranas**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/alertas` | Bearer | Lista de alertas (filtrable). |
| `POST` | `/alertas/{alerta_id}/reconocer` | **analista+** | Reconoce una alerta. |

### `GET /alertas`

**Parámetros:** `estado` (`abierta` \| `en_revision` \| `reconocida` \| `cerrada`),
`severidad` (`info` \| `baja` \| `media` \| `alta` \| `critica`).

```json
{
  "items": [
    {
      "id": "al1", "titulo": "Pico de menciones detectado",
      "descripcion": "Incremento del 142% en menciones sobre 'Elecciones' en 24h.",
      "tipo": "pico_menciones", "severidad": "alta", "estado": "abierta",
      "valor": 142.0, "created_at": "2026-06-18T13:00:00"
    }
  ]
}
```

### `POST /alertas/{alerta_id}/reconocer`

Requiere rol **analista** o superior.

```json
{ "id": "al1", "estado": "reconocida", "ok": true }
```

---

## 15. Fuentes

Prefijo: `/api/v1/fuentes`. Módulo administrativo **Fuentes**.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/fuentes` | Bearer | Lista las fuentes configuradas. |
| `POST` | `/fuentes` | **editor+** | Crea una fuente (`201`). |
| `PUT` | `/fuentes/{fuente_id}` | **editor+** | Actualiza una fuente. |
| `DELETE` | `/fuentes/{fuente_id}` | **admin** | Elimina una fuente (`204`). |

### `GET /fuentes`

```json
{
  "items": [
    {
      "id": "f4", "nombre": "Efecto Cocuyo", "tipo": "portal", "alcance": "nacional",
      "credibilidad": 78, "verificada": true, "estado": "activa",
      "url": "https://example.org/efectococuyo",
      "articulos_30d": 210, "ultima_lectura": "2026-06-18T12:30:00"
    }
  ]
}
```

### `POST /fuentes`

**Cuerpo** (`FuenteCreate`):

```json
{
  "nombre": "Nuevo Portal", "tipo": "portal",
  "url": "https://nuevoportal.example", "rss_url": "https://nuevoportal.example/feed/",
  "alcance": "regional", "idioma": "es", "pais": "VE",
  "credibilidad": 65, "verificada": false, "estado": "activa",
  "notas": "Fuente verificada manualmente."
}
```

Respuesta `201`:

```json
{
  "id": "8c2a...d1", "nombre": "Nuevo Portal", "tipo": "portal",
  "url": "https://nuevoportal.example", "rss_url": "https://nuevoportal.example/feed/",
  "alcance": "regional", "idioma": "es", "pais": "VE",
  "credibilidad": 65, "verificada": false, "estado": "activa",
  "notas": "Fuente verificada manualmente.",
  "articulos_30d": 0, "ultima_lectura": null
}
```

### `PUT /fuentes/{fuente_id}`

**Cuerpo** (`FuenteUpdate`, todos opcionales): `nombre`, `tipo`, `url`, `rss_url`,
`alcance`, `credibilidad`, `verificada`, `estado`, `notas`. Devuelve el `id` y los
campos enviados (no nulos).

### `DELETE /fuentes/{fuente_id}`

Requiere rol **admin**. Respuesta `204` sin cuerpo.

---

## 16. Reportes

Prefijo: `/api/v1/reportes`. Módulo **Informes Ejecutivos**.
**PDF es el único formato de exportación.**

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/reportes` | Bearer | Lista de informes archivados. |
| `POST` | `/reportes/generar` | **analista+** | Genera ahora el PDF ejecutivo (`201`). |
| `GET` | `/reportes/{reporte_id}` | Bearer | Metadatos de un informe. |
| `GET` | `/reportes/{reporte_id}/pdf` | Bearer | Descarga el binario PDF (`application/pdf`). |

### `GET /reportes`

```json
{
  "items": [
    {
      "id": "rep1",
      "titulo": "Informe Ejecutivo Diario — 18/06/2026",
      "tipo": "ejecutivo_diario", "estado": "completado",
      "periodo_hasta": "2026-06-18",
      "archivo_bytes": 845210, "created_at": "2026-06-18"
    }
  ]
}
```

### `POST /reportes/generar`

Requiere rol **analista** o superior. **Cuerpo** (`ReporteGenerar`):
`{ "tipo": "ejecutivo_diario", "periodo_desde": null, "periodo_hasta": null }`
(`tipo`: `ejecutivo_diario` \| `semanal` \| `ad_hoc`).

```json
{
  "titulo": "Informe Ejecutivo Diario — 18/06/2026",
  "tipo": "ejecutivo_diario",
  "estado": "completado",
  "archivo_path": "./storage/reports/informe_ejecutivo_20260618.pdf",
  "archivo_bytes": 845210,
  "pdf_sha256": "3b9a4f2c8e1d...",
  "completado_en": "2026-06-18T06:00:12"
}
```

### `GET /reportes/{reporte_id}/pdf`

Devuelve el binario con `Content-Type: application/pdf` (cabecera
`Content-Disposition: attachment`). Si no hay archivo en disco, se genera al vuelo.

```bash
curl -s -L "https://host/api/v1/reportes/rep1/pdf" \
  -H "Authorization: Bearer <token>" -o informe.pdf
```

---

## 17. Búsqueda

Prefijo: `/api/v1/buscar`. Módulo **Centro de Inteligencia Digital** / buscador ⌘K.

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/buscar` | Bearer | Búsqueda unificada (actores, narrativas, fuentes, temas). |

### `GET /buscar`

**Parámetro:** `q` (requerido, mínimo 2 caracteres).

```bash
curl -s "https://host/api/v1/buscar?q=maria" -H "Authorization: Bearer <token>"
```

```json
{
  "items": [
    { "tipo": "Actor", "label": "María Corina Machado", "sub": "Líder político",
      "view": "actors" }
  ]
}
```

---

## 18. ETL

Prefijo: `/api/v1/etl`. Observabilidad del pipeline (ver
[MANUAL_TECNICO.md §7](MANUAL_TECNICO.md#7-motores-de-análisis-y-pipeline-etl)).

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/etl/estado` | Bearer | Últimas ejecuciones + próximo ciclo programado. |

### `GET /etl/estado`

```json
{
  "runs": [
    { "job": "ingest", "estado": "completado", "items_in": 540, "items_out": 512,
      "items_error": 3, "duracion_ms": 41200, "iniciado_en": "2026-06-18T05:00:01" },
    { "job": "clean", "estado": "completado", "items_in": 512, "items_out": 512,
      "items_error": 0, "duracion_ms": 8800, "iniciado_en": "2026-06-18T05:01:00" },
    { "job": "classify", "estado": "completado", "items_in": 512, "items_out": 512,
      "items_error": 0, "duracion_ms": 15200, "iniciado_en": "2026-06-18T05:02:00" },
    { "job": "analyze", "estado": "completado", "items_in": 512, "items_out": 512,
      "items_error": 0, "duracion_ms": 22400, "iniciado_en": "2026-06-18T05:05:00" },
    { "job": "aggregate", "estado": "completado", "items_in": 512, "items_out": 1,
      "items_error": 0, "duracion_ms": 5100, "iniciado_en": "2026-06-18T05:08:00" }
  ],
  "schedule": {
    "etl_cron": "0 5 * * *",
    "report_cron": "0 6 * * *",
    "timezone": "America/Caracas"
  },
  "next_run": "05:00 America/Caracas"
}
```

---

## 19. Comparativos

Prefijo: `/api/v1/comparativos`. Módulo **Comparativos Históricos**
(comparte módulo con Tendencias).

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/comparativos` | Bearer | Comparación de volumen por tema (período vs. anterior). |
| `GET` | `/comparativos/correlaciones` | Bearer | Fuerza de correlación entre temas. |

### `GET /comparativos`

**Parámetros:** `desde`, `hasta`, `vs`.

```json
{
  "actual":   [ { "tema": "Elecciones", "valor": 512 }, { "tema": "Economía", "valor": 287 } ],
  "anterior": [ { "tema": "Elecciones", "valor": 433 }, { "tema": "Economía", "valor": 301 } ]
}
```

### `GET /comparativos/correlaciones`

```json
{
  "items": [
    { "a": "Elecciones", "b": "Negociación", "r": 0.82 },
    { "a": "Servicios", "b": "Economía", "r": 0.74 }
  ]
}
```

---

## 20. Matriz de roles (RBAC)

El control de acceso es **jerárquico**:
`lector (0) < editor (1) < analista (2) < admin (3)`. Un rol superior hereda los
permisos de los inferiores. En modo DEMO (no producción) las restricciones de rol no
se aplican.

| Operación | Rol mínimo |
|-----------|-----------|
| Lectura de dashboard y módulos | lector |
| Descarga de informes PDF | lector |
| Crear / actualizar fuentes (`POST`/`PUT /fuentes`) | editor |
| Eliminar fuentes (`DELETE /fuentes/{id}`) | admin |
| Generar informes (`POST /reportes/generar`) | analista |
| Reconocer alertas (`POST /alertas/{id}/reconocer`) | analista |
| Administración de usuarios y auditoría | admin |

---

## 21. Documentos relacionados

- [ARQUITECTURA.md](ARQUITECTURA.md) — componentes y modelo de datos.
- [MANUAL_TECNICO.md](MANUAL_TECNICO.md) — instalación, configuración y motores.
- [MANUAL_USUARIO.md](MANUAL_USUARIO.md) — guía de uso de los 12 módulos.
- [DESPLIEGUE.md](DESPLIEGUE.md) — despliegue local y producción.
- [USO_ETICO.md](USO_ETICO.md) — política de uso ético y legal.
