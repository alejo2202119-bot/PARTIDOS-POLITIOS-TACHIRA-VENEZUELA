"""Sentiment analysis service (pluggable provider).

Default provider ``local`` uses a lightweight Spanish lexicon scorer with no
external dependencies, so analysis always works offline. When
``AI_PROVIDER='anthropic'`` and a key is configured, ``analyze_with_anthropic``
can be used for higher-quality scoring (model taken from settings).
"""

from __future__ import annotations

import re
import unicodedata

from app.config import settings
from app.schemas import SentimentResult

# Compact Spanish polarity lexicon (illustrative — extend for production).
_POSITIVE = {
    "acuerdo", "avance", "logro", "esperanza", "unidad", "mejora", "apoyo", "crecimiento",
    "libertad", "paz", "dialogo", "solucion", "progreso", "victoria", "exito", "fortaleza",
    "transparencia", "reconciliacion", "estabilidad", "oportunidad", "positivo", "favorable",
}
_NEGATIVE = {
    "crisis", "represion", "detencion", "conflicto", "denuncia", "violencia", "corrupcion",
    "fraude", "escasez", "protesta", "abuso", "amenaza", "censura", "ruptura", "fracaso",
    "inflacion", "colapso", "tension", "rechazo", "negativo", "ilegitimo", "persecucion",
    "bloqueo", "sancion", "irregularidad",
}
_EMOTION_HINTS = {
    "alegria": {"esperanza", "logro", "victoria", "exito", "unidad"},
    "enojo": {"corrupcion", "abuso", "represion", "fraude", "rechazo"},
    "miedo": {"amenaza", "violencia", "crisis", "colapso", "persecucion"},
    "tristeza": {"escasez", "fracaso", "ruptura", "detencion"},
}


def _normalize(text: str) -> list[str]:
    text = text.lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-záéíóúñ]+", text)


def analyze_local(text: str) -> SentimentResult:
    """Lexicon-based polarity scoring in [-1, 1]."""
    tokens = _normalize(text or "")
    if not tokens:
        return SentimentResult(etiqueta="neutral", score=0.0, confianza=0.2, modelo="local-lexicon")

    pos = sum(1 for t in tokens if t in _POSITIVE)
    neg = sum(1 for t in tokens if t in _NEGATIVE)
    total = pos + neg
    score = 0.0 if total == 0 else (pos - neg) / total
    # Confidence grows with the share of polarity-bearing tokens.
    confianza = round(min(0.95, 0.4 + total / max(len(tokens), 1)), 3)

    if score > 0.15:
        etiqueta = "positivo"
    elif score < -0.15:
        etiqueta = "negativo"
    else:
        etiqueta = "neutral"

    emociones = {}
    tset = set(tokens)
    for emo, words in _EMOTION_HINTS.items():
        hits = len(tset & words)
        if hits:
            emociones[emo] = round(min(1.0, hits / 3), 2)

    return SentimentResult(
        etiqueta=etiqueta, score=round(score, 3), confianza=confianza,
        emociones=emociones, modelo="local-lexicon",
    )


async def analyze_with_anthropic(text: str) -> SentimentResult:  # pragma: no cover - needs key
    """Optional higher-quality scoring via the Anthropic Messages API.

    Falls back to the local scorer on any error or when no key is configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        return analyze_local(text)
    try:
        import json

        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=200,
            system=(
                "Eres un analista de sentimiento de medios. Devuelve SOLO JSON: "
                '{"etiqueta":"positivo|neutral|negativo","score":-1..1,"confianza":0..1}. '
                "Analiza el tono del texto periodístico sobre asuntos públicos."
            ),
            messages=[{"role": "user", "content": text[:4000]}],
        )
        data = json.loads(msg.content[0].text)
        return SentimentResult(
            etiqueta=data.get("etiqueta", "neutral"),
            score=float(data.get("score", 0.0)),
            confianza=float(data.get("confianza", 0.6)),
            modelo=settings.ANTHROPIC_MODEL,
        )
    except Exception:
        return analyze_local(text)


async def analyze(text: str) -> SentimentResult:
    """Analyze using the configured provider."""
    if settings.AI_PROVIDER == "anthropic":
        return await analyze_with_anthropic(text)
    return analyze_local(text)
