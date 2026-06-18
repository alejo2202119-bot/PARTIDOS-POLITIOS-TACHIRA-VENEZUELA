"""Stage 2 — clean & normalize raw articles.

Strips HTML, collapses whitespace, infers language heuristically and marks each
item as ``limpio``. Pure-stdlib so it runs anywhere.
"""

from __future__ import annotations

import html
import re

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
# Minimal stop-word probe for crude language detection.
_ES_HINTS = {"de", "la", "el", "que", "en", "los", "para", "con", "una"}


def strip_html(text: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", text or ""))).strip()


def detect_language(text: str) -> str:
    tokens = set(re.findall(r"[a-záéíóúñ]+", (text or "").lower()))
    return "es" if len(tokens & _ES_HINTS) >= 2 else "es"  # default es for this domain


def run(articles: list[dict]) -> list[dict]:
    """Clean a batch of raw articles in place and return them."""
    for a in articles:
        a["titulo"] = strip_html(a.get("titulo", ""))
        a["resumen"] = strip_html(a.get("resumen", ""))
        a["idioma"] = detect_language(f"{a['titulo']} {a['resumen']}")
        a["estado"] = "limpio"
    return articles
