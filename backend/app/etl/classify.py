"""Stage 3 — classify articles by topic, geography and relevance.

Keyword-based topic assignment and a simple relevance heuristic. Marks each
item ``clasificado``. Topic keyword maps mirror ``database/seed.sql`` ``temas``.
"""

from __future__ import annotations

import re
import unicodedata

TOPIC_KEYWORDS = {
    "Elecciones": {"eleccion", "elecciones", "comicios", "voto", "candidat", "primarias", "electoral"},
    "Derechos Humanos": {"ddhh", "derechos", "libertad", "detencion", "preso", "represion"},
    "Economía": {"inflacion", "salario", "dolar", "economia", "precios", "empleo"},
    "Servicios Públicos": {"electricidad", "agua", "gasolina", "servicio", "apagon"},
    "Negociación Política": {"dialogo", "negociacion", "acuerdo", "mesa", "mediacion"},
    "Migración": {"migracion", "migrante", "frontera", "retorno"},
    "Seguridad": {"seguridad", "delincuencia", "orden", "violencia"},
}

ESTADOS_VE = [
    "Táchira", "Zulia", "Distrito Capital", "Miranda", "Carabobo", "Lara", "Mérida",
    "Trujillo", "Bolívar", "Anzoátegui", "Aragua", "Falcón",
]


def _norm(text: str) -> str:
    text = (text or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def classify_topic(text: str) -> str | None:
    n = _norm(text)
    best, score = None, 0
    for tema, kws in TOPIC_KEYWORDS.items():
        hits = sum(1 for k in kws if k in n)
        if hits > score:
            best, score = tema, hits
    return best


def classify_geo(text: str) -> str | None:
    for estado in ESTADOS_VE:
        if _norm(estado) in _norm(text):
            return estado
    return None


def relevance(text: str, topic: str | None) -> str:
    n = _norm(text)
    if any(w in n for w in ("urgente", "crisis", "emergencia")):
        return "critica"
    if topic in ("Elecciones", "Derechos Humanos"):
        return "alta"
    if topic:
        return "media"
    return "baja"


def run(articles: list[dict]) -> list[dict]:
    for a in articles:
        text = f"{a.get('titulo','')} {a.get('resumen','')}"
        a["tema"] = classify_topic(text)
        a["estado_geo"] = classify_geo(text)
        a["relevancia"] = relevance(text, a["tema"])
        a["estado"] = "clasificado"
    return articles
