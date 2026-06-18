"""Stage 5 — aggregate analyzed articles into trends, KPIs and alerts.

Computes per-topic daily counts, a KPI snapshot for the day, and evaluates the
alert rules engine. Returns a summary dict; persistence is handled by the
pipeline when the DB is reachable.
"""

from __future__ import annotations

from collections import Counter
from datetime import date

from app.services import alerts_engine, trends


def run(articles: list[dict]) -> dict:
    """Aggregate a batch of analyzed articles into a daily summary."""
    total = len(articles)
    scores = [a.get("score", 0.0) for a in articles if "score" in a]
    sentimiento_global = round(sum(scores) / len(scores), 3) if scores else 0.0

    topic_counts = Counter(a.get("tema") for a in articles if a.get("tema"))
    geo_counts = Counter(a.get("estado_geo") for a in articles if a.get("estado_geo"))
    reach = trends.estimated_reach(articles)

    total_mentions = sum(len(a.get("menciones", [])) for a in articles)

    # Territorial concentration (share of top state) for the alert engine.
    concentracion = {}
    if geo_counts:
        top_state, top_n = geo_counts.most_common(1)[0]
        concentracion[top_state] = top_n / max(total, 1)

    metrics = {
        "crecimiento_menciones_pct": None,  # requires history; filled in prod
        "delta_sentimiento": None,
        "narrativas": [],
        "concentracion": concentracion,
    }
    alerts = alerts_engine.evaluate(metrics)

    snapshot = {
        "fecha": date.today().isoformat(),
        "total_articulos": total,
        "total_menciones": total_mentions,
        "sentimiento_global": sentimiento_global,
        "alcance_total": reach,
        "por_tema": dict(topic_counts),
        "por_estado": dict(geo_counts),
    }
    return {"snapshot": snapshot, "alertas": alerts}
