"""Narrative detection via keyword-overlap clustering.

Dependency-light: groups recent articles whose normalized keyword sets overlap
above a threshold, then flags clusters with recent growth as "emergent".
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

_STOP = {
    "de", "la", "el", "en", "y", "a", "los", "las", "del", "que", "por", "con", "un", "una",
    "para", "se", "su", "al", "lo", "como", "mas", "pero", "sus", "le", "ya", "o", "este",
    "sobre", "entre", "tras", "ante", "es", "son", "fue", "ha", "han", "the",
}


def _keywords(text: str, top: int = 8) -> set[str]:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    words = [w for w in re.findall(r"[a-z]{4,}", text) if w not in _STOP]
    return {w for w, _ in Counter(words).most_common(top)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster(articulos: list[dict], threshold: float = 0.28) -> list[dict]:
    """Cluster articles into narratives.

    Each article dict needs ``titulo`` and optionally ``resumen``.
    Returns a list of narrative dicts with keywords, size and member ids.
    """
    kw = [(_keywords(f"{a.get('titulo','')} {a.get('resumen','')}"), a) for a in articulos]
    clusters: list[dict] = []

    for keys, art in kw:
        placed = False
        for cl in clusters:
            if _jaccard(keys, cl["_keys"]) >= threshold:
                cl["_keys"] |= keys
                cl["miembros"].append(art.get("id"))
                cl["total_articulos"] += 1
                cl["alcance_estimado"] += art.get("alcance_estimado", 0) or 0
                placed = True
                break
        if not placed:
            clusters.append({
                "_keys": set(keys),
                "titulo": art.get("titulo", "Narrativa"),
                "miembros": [art.get("id")],
                "total_articulos": 1,
                "alcance_estimado": art.get("alcance_estimado", 0) or 0,
            })

    out = []
    for cl in clusters:
        out.append({
            "titulo": cl["titulo"],
            "palabras_clave": sorted(cl["_keys"])[:6],
            "total_articulos": cl["total_articulos"],
            "alcance_estimado": cl["alcance_estimado"],
            "miembros": cl["miembros"],
            "emergente": cl["total_articulos"] >= 3,  # heuristic; refined in aggregate
        })
    out.sort(key=lambda c: c["total_articulos"], reverse=True)
    return out
