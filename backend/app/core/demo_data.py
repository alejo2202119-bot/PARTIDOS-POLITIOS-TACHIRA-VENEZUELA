"""In-memory representative dataset (Táchira / Venezuela theme).

This powers every read endpoint when the database is empty or unreachable, so
the API is always demoable. All sentiment / mention figures are SYNTHETIC and
illustrative — not real measurements. Mirrors the frontend ``mock.js`` theme.
"""

from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta

random.seed(2026)  # deterministic demo output

TODAY = date.today()


def _series(days: int, base: float, vol: float, trend: float = 0.0) -> list[dict]:
    out, v = [], base
    for i in range(days - 1, -1, -1):
        d = TODAY - timedelta(days=i)
        v = max(0.0, v + random.uniform(-vol, vol) + trend)
        out.append({"x": d.isoformat(), "y": round(v)})
    return out


TEMAS = [
    {"id": "t1", "nombre": "Elecciones", "color": "#6366f1"},
    {"id": "t2", "nombre": "Derechos Humanos", "color": "#ef4444"},
    {"id": "t3", "nombre": "Economía", "color": "#22c55e"},
    {"id": "t4", "nombre": "Servicios Públicos", "color": "#f59e0b"},
    {"id": "t5", "nombre": "Negociación Política", "color": "#06b6d4"},
    {"id": "t6", "nombre": "Migración", "color": "#a855f7"},
    {"id": "t7", "nombre": "Seguridad", "color": "#64748b"},
]

ESTADOS = [
    {"id": "e-tac", "estado": "Táchira", "latitud": 7.7669, "longitud": -72.2250},
    {"id": "e-zul", "estado": "Zulia", "latitud": 10.6427, "longitud": -71.6125},
    {"id": "e-dc", "estado": "Distrito Capital", "latitud": 10.4806, "longitud": -66.9036},
    {"id": "e-mir", "estado": "Miranda", "latitud": 10.3417, "longitud": -67.0407},
    {"id": "e-car", "estado": "Carabobo", "latitud": 10.1620, "longitud": -68.0077},
    {"id": "e-lar", "estado": "Lara", "latitud": 10.0731, "longitud": -69.3220},
    {"id": "e-mer", "estado": "Mérida", "latitud": 8.5897, "longitud": -71.1561},
    {"id": "e-tru", "estado": "Trujillo", "latitud": 9.3667, "longitud": -70.4333},
    {"id": "e-bol", "estado": "Bolívar", "latitud": 8.1222, "longitud": -63.5497},
    {"id": "e-anz", "estado": "Anzoátegui", "latitud": 10.1340, "longitud": -64.6853},
]
for e in ESTADOS:
    e["articulos"] = random.randint(60, 400)
    e["sentimiento_prom"] = round(random.uniform(-0.35, 0.2), 3)


_ACTORES_BASE = [
    ("María Corina Machado", "Líder político", "VV"),
    ("Edmundo González Urrutia", "Figura pública", "PUD"),
    ("Henrique Capriles", "Dirigente", "PJ"),
    ("Manuel Rosales", "Gobernador", "UNT"),
    ("Juan Pablo Guanipa", "Dirigente", "PJ"),
    ("Laidy Gómez", "Dirigente regional", "AD"),
    ("Roberto Enríquez", "Dirigente", "COPEI"),
    ("Tomás Guanipa", "Dirigente", "PJ"),
]
ACTORES = []
for i, (n, c, o) in enumerate(_ACTORES_BASE):
    ACTORES.append({
        "id": f"a{i+1}", "nombre": n, "cargo": c, "organizacion": o,
        "menciones": max(20, random.randint(40, 480) - i * 20),
        "sentimiento_prom": round(random.uniform(-0.4, 0.4), 3),
        "alcance_estimado": random.randint(120_000, 2_400_000),
        "trend": [p["y"] for p in _series(14, random.randint(20, 60), 8, random.uniform(-1, 2))],
    })
ACTORES.sort(key=lambda a: a["menciones"], reverse=True)


_FUENTES_BASE = [
    ("El Nacional", "medio", "nacional", 70), ("El Universal", "medio", "nacional", 68),
    ("Tal Cual", "medio", "nacional", 72), ("Efecto Cocuyo", "portal", "nacional", 78),
    ("Runrun.es", "portal", "nacional", 75), ("La Patilla", "portal", "nacional", 66),
    ("Crónica.Uno", "portal", "nacional", 77), ("Diario La Nación", "medio", "regional", 69),
    ("La Prensa del Táchira", "medio", "regional", 60), ("Diario de Los Andes", "medio", "regional", 62),
    ("Reuters (AL)", "agencia", "internacional", 85), ("France 24 Español", "medio", "internacional", 82),
]
FUENTES = []
for i, (n, t, al, cr) in enumerate(_FUENTES_BASE):
    FUENTES.append({
        "id": f"f{i+1}", "nombre": n, "tipo": t, "alcance": al, "credibilidad": cr,
        "verificada": cr >= 65, "estado": "activa" if random.random() > 0.12 else "pausada",
        "url": "https://example.org/" + "".join(ch for ch in n.lower() if ch.isalpha()),
        "articulos_30d": random.randint(20, 320),
        "ultima_lectura": (datetime.utcnow() - timedelta(minutes=random.randint(1, 600))).isoformat(),
    })


_NARR_BASE = [
    ("Llamado a la unidad opositora de cara al proceso electoral", "t1", "neutral", "alta", True),
    ("Crisis de servicios públicos en la región andina", "t4", "negativo", "alta", False),
    ("Debate sobre condiciones electorales y observación", "t1", "neutral", "media", False),
    ("Situación de derechos y libertades civiles", "t2", "negativo", "critica", True),
    ("Expectativas económicas y poder adquisitivo", "t3", "negativo", "media", False),
    ("Dinámica migratoria y retorno en la frontera", "t6", "neutral", "media", False),
    ("Diálogo y posibles acuerdos políticos", "t5", "positivo", "media", False),
]
NARRATIVAS = []
for i, (titulo, tema, sent, rel, emerg) in enumerate(_NARR_BASE):
    NARRATIVAS.append({
        "id": f"n{i+1}", "titulo": titulo, "tema_id": tema, "sentimiento": sent,
        "relevancia": rel, "emergente": emerg,
        "total_articulos": random.randint(8, 140),
        "alcance_estimado": random.randint(80_000, 1_800_000),
        "variacion": round(random.uniform(-30, 180), 1),
        "palabras_clave": ["unidad", "elecciones", "región", "frontera", "derechos"][: random.randint(3, 5)],
        "serie": _series(14, random.randint(5, 25), 5, 2 if emerg else 0.2),
        "ultima_vista": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat(),
    })


_TITULARES = [
    "Dirigentes opositores presentan agenda regional en San Cristóbal",
    "Análisis: cobertura mediática sobre el proceso electoral",
    "Organizaciones civiles publican comunicado sobre servicios públicos",
    "Foro público aborda economía y empleo en la región andina",
    "Cobertura internacional sobre la situación política venezolana",
    "Actividad partidista en municipios fronterizos del Táchira",
    "Debate público sobre derechos y participación ciudadana",
    "Medios regionales reportan jornada de organización vecinal",
]
_REL = ["baja", "media", "alta", "critica"]
ARTICULOS = []
for i in range(60):
    f = random.choice(FUENTES)
    t = random.choice(TEMAS)
    e = random.choice(ESTADOS)
    a = random.choice(ACTORES)
    score = round(random.uniform(-1, 1), 3)
    ARTICULOS.append({
        "id": f"art{i+1}",
        "titulo": _TITULARES[i % len(_TITULARES)],
        "resumen": "Resumen sintético de demostración para el panel de monitoreo de información pública.",
        "fuente": f["nombre"], "fuente_id": f["id"], "tipo_fuente": f["tipo"],
        "tema": t["nombre"], "tema_color": t["color"], "estado": e["estado"], "actor": a["nombre"],
        "publicado_en": (datetime.utcnow() - timedelta(minutes=i * random.randint(20, 90))).isoformat(),
        "relevancia": _REL[min(3, random.randint(0, 3))],
        "sentimiento": "positivo" if score > 0.15 else "negativo" if score < -0.15 else "neutral",
        "score": score,
        "alcance_estimado": random.randint(2_000, 180_000),
        "url": "#",
    })


ALERTAS = [
    {"id": "al1", "titulo": "Pico de menciones detectado", "descripcion": "Incremento del 142% en menciones sobre 'Elecciones' en 24h.", "tipo": "pico_menciones", "severidad": "alta", "estado": "abierta", "valor": 142.0, "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()},
    {"id": "al2", "titulo": "Narrativa emergente", "descripcion": "Nueva narrativa sobre servicios públicos ganando tracción regional.", "tipo": "narrativa_emergente", "severidad": "media", "estado": "en_revision", "valor": 38.0, "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat()},
    {"id": "al3", "titulo": "Caída de sentimiento", "descripcion": "El sentimiento global descendió 0.18 puntos respecto a la semana previa.", "tipo": "sentimiento", "severidad": "media", "estado": "abierta", "valor": -0.18, "created_at": (datetime.utcnow() - timedelta(hours=11)).isoformat()},
    {"id": "al4", "titulo": "Concentración territorial", "descripcion": "Concentración inusual de cobertura en municipios fronterizos del Táchira.", "tipo": "territorial", "severidad": "baja", "estado": "reconocida", "valor": 27.0, "created_at": (datetime.utcnow() - timedelta(hours=26)).isoformat()},
    {"id": "al5", "titulo": "Alta correlación de eventos", "descripcion": "Correlación elevada entre cobertura de 'Negociación' y 'Elecciones'.", "tipo": "correlacion", "severidad": "info", "estado": "abierta", "valor": 0.82, "created_at": (datetime.utcnow() - timedelta(hours=40)).isoformat()},
]

REPORTES = []
for i in range(8):
    d = TODAY - timedelta(days=i)
    REPORTES.append({
        "id": f"rep{i+1}",
        "titulo": f"Informe Ejecutivo Diario — {d.strftime('%d/%m/%Y')}",
        "tipo": "ejecutivo_diario", "estado": "completado",
        "periodo_hasta": d.isoformat(),
        "archivo_bytes": random.randint(420_000, 1_200_000),
        "created_at": d.isoformat(),
    })


CORRELACIONES = [
    {"a": "Elecciones", "b": "Negociación", "r": 0.82},
    {"a": "Servicios", "b": "Economía", "r": 0.74},
    {"a": "Migración", "b": "Economía", "r": 0.61},
    {"a": "DDHH", "b": "Negociación", "r": 0.57},
    {"a": "Seguridad", "b": "Migración", "r": 0.49},
]

EMERGENTES = [
    {"tema": "Observación electoral", "crecimiento": 214, "menciones": 342},
    {"tema": "Servicios en la frontera", "crecimiento": 158, "menciones": 221},
    {"tema": "Unidad opositora", "crecimiento": 96, "menciones": 588},
    {"tema": "Poder adquisitivo", "crecimiento": 73, "menciones": 410},
    {"tema": "Retorno migratorio", "crecimiento": 41, "menciones": 187},
]

_SCORE = -0.06
KPIS = {
    "fecha": TODAY.isoformat(),
    "total_articulos": 1248, "total_menciones": 3962, "fuentes_activas": 11,
    "sentimiento_global": _SCORE, "narrativas_activas": 7, "narrativas_emergentes": 2,
    "alertas_abiertas": len([a for a in ALERTAS if a["estado"] == "abierta"]),
    "alcance_total": 18_940_000,
    "deltas": {"total_articulos": 12.4, "total_menciones": 18.1, "fuentes_activas": 0.0,
               "sentimiento_global": -8.2, "alcance_total": 9.7},
    "spark": {
        "total_articulos": [p["y"] for p in _series(14, 80, 18, 1)],
        "total_menciones": [p["y"] for p in _series(14, 260, 40, 2)],
        "alcance_total": [p["y"] for p in _series(14, 1_100_000, 200_000, 10_000)],
        "sentimiento_global": [round((p["y"] - 50) / 100, 3) for p in _series(14, 50, 8)],
    },
}

SENTIMIENTO = {
    "resumen": {"positivo": 28, "neutral": 41, "negativo": 31, "score_global": _SCORE},
    "series": [
        {"name": t["nombre"], "color": t["color"],
         "data": [{"x": p["x"], "y": round(random.uniform(-0.5, 0.4), 2)} for p in _series(14, 50, 10)]}
        for t in TEMAS[:4]
    ],
}

TENDENCIAS = {
    "series": [
        {"name": t["nombre"], "color": t["color"], "data": _series(30, random.randint(20, 90), 10, random.uniform(-1, 2))}
        for t in TEMAS
    ],
    "emergentes": EMERGENTES,
}


def overview() -> dict:
    return {
        "actores": ACTORES[:5],
        "narrativas": NARRATIVAS[:4],
        "alertas": ALERTAS[:4],
        "sentimiento": SENTIMIENTO["resumen"],
    }


def buscar(q: str) -> list[dict]:
    ql = q.lower()
    out: list[dict] = []
    for a in ACTORES:
        if ql in a["nombre"].lower():
            out.append({"tipo": "Actor", "label": a["nombre"], "sub": a["cargo"], "view": "actors"})
    for n in NARRATIVAS:
        if ql in n["titulo"].lower():
            out.append({"tipo": "Narrativa", "label": n["titulo"], "sub": "Narrativa", "view": "narratives"})
    for f in FUENTES:
        if ql in f["nombre"].lower():
            out.append({"tipo": "Fuente", "label": f["nombre"], "sub": f["tipo"], "view": "sources"})
    return out[:10]
