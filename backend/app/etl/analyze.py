"""Stage 4 — analyze articles: sentiment + actor/organization mentions.

Runs the sentiment service over each item and matches known actor names/aliases
to create mentions. Marks each item ``analizado``.
"""

from __future__ import annotations

import unicodedata

from app.services import sentiment as sent_svc


def _norm(text: str) -> str:
    text = (text or "").lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def extract_mentions(text: str, actores: list[dict]) -> list[dict]:
    """Match actor names / aliases against the public text."""
    n = _norm(text)
    found = []
    for a in actores:
        names = [a.get("nombre", "")] + list(a.get("aliases", []) or [])
        if any(_norm(name) and _norm(name) in n for name in names):
            found.append({"actor_id": a.get("id"), "nombre": a.get("nombre")})
    return found


async def run(articles: list[dict], actores: list[dict] | None = None) -> list[dict]:
    actores = actores or []
    for a in articles:
        text = f"{a.get('titulo','')} {a.get('resumen','')}"
        result = await sent_svc.analyze(text)
        a["sentimiento"] = result.etiqueta
        a["score"] = result.score
        a["confianza"] = result.confianza
        a["menciones"] = extract_mentions(text, actores)
        a["estado"] = "analizado"
    return articles
