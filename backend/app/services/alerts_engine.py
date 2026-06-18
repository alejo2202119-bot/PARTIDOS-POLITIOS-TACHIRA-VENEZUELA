"""Rule-based early-warning engine.

Evaluates simple, transparent thresholds over aggregated metrics and emits
alert dicts. Rules: mention spikes, sentiment drops, emergent narratives,
territorial concentration. Thresholds are configurable per call.
"""

from __future__ import annotations

from datetime import datetime

DEFAULT_RULES = {
    "pico_menciones_pct": 100.0,   # +100% day-over-day → alert
    "caida_sentimiento": -0.15,    # absolute drop in mean score
    "narrativa_emergente_pct": 80.0,
    "concentracion_territorial_pct": 60.0,  # share of coverage in one state
}


def _sev(value: float, t1: float, t2: float, t3: float) -> str:
    if value >= t3:
        return "critica"
    if value >= t2:
        return "alta"
    if value >= t1:
        return "media"
    return "baja"


def evaluate(metrics: dict, rules: dict | None = None) -> list[dict]:
    """Return a list of triggered alerts given a metrics snapshot.

    ``metrics`` may contain: ``crecimiento_menciones_pct``,
    ``delta_sentimiento``, ``narrativas`` (list with ``crecimiento``),
    ``concentracion`` (dict estado→share).
    """
    rules = {**DEFAULT_RULES, **(rules or {})}
    alerts: list[dict] = []
    now = datetime.utcnow().isoformat()

    g = metrics.get("crecimiento_menciones_pct")
    if g is not None and g >= rules["pico_menciones_pct"]:
        alerts.append({
            "titulo": "Pico de menciones detectado",
            "descripcion": f"Incremento del {g:.0f}% en menciones respecto al período previo.",
            "tipo": "pico_menciones", "severidad": _sev(g, 100, 200, 400),
            "valor": g, "estado": "abierta", "created_at": now,
        })

    d = metrics.get("delta_sentimiento")
    if d is not None and d <= rules["caida_sentimiento"]:
        alerts.append({
            "titulo": "Caída de sentimiento",
            "descripcion": f"El sentimiento global descendió {abs(d):.2f} puntos.",
            "tipo": "sentimiento", "severidad": _sev(abs(d), 0.15, 0.3, 0.5),
            "valor": d, "estado": "abierta", "created_at": now,
        })

    for n in metrics.get("narrativas", []):
        if n.get("crecimiento", 0) >= rules["narrativa_emergente_pct"]:
            alerts.append({
                "titulo": "Narrativa emergente",
                "descripcion": f"La narrativa '{n.get('tema', n.get('titulo',''))}' crece {n['crecimiento']:.0f}%.",
                "tipo": "narrativa_emergente", "severidad": "media",
                "valor": n["crecimiento"], "estado": "abierta", "created_at": now,
            })

    conc = metrics.get("concentracion", {})
    for estado, share in conc.items():
        if share * 100 >= rules["concentracion_territorial_pct"]:
            alerts.append({
                "titulo": "Concentración territorial",
                "descripcion": f"Concentración del {share*100:.0f}% de la cobertura en {estado}.",
                "tipo": "territorial", "severidad": "baja",
                "valor": share * 100, "estado": "abierta", "created_at": now,
            })

    return alerts
