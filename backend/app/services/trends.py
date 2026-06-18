"""Trend aggregation helpers: growth %, emerging topics, estimated reach."""

from __future__ import annotations

from collections import defaultdict


def growth_pct(current: float, previous: float) -> float:
    """Percentage change from ``previous`` to ``current`` (safe for zero)."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


def aggregate_daily(rows: list[dict], key: str = "tema") -> dict[str, list[dict]]:
    """Group ``rows`` (each with a date ``fecha`` and ``key``) into daily series."""
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        buckets[r[key]][r["fecha"]] += 1
    series = {}
    for name, days in buckets.items():
        series[name] = [{"x": d, "y": days[d]} for d in sorted(days)]
    return series


def emerging(series: dict[str, list[dict]], window: int = 7) -> list[dict]:
    """Rank topics by recent growth (last ``window`` vs prior ``window``)."""
    out = []
    for name, pts in series.items():
        ys = [p["y"] for p in pts]
        cur = sum(ys[-window:])
        prev = sum(ys[-2 * window : -window]) if len(ys) >= 2 * window else 0
        out.append({"tema": name, "menciones": cur, "crecimiento": growth_pct(cur, prev)})
    out.sort(key=lambda x: x["crecimiento"], reverse=True)
    return out


def estimated_reach(articulos: list[dict]) -> int:
    """Sum of estimated reach across a set of articles."""
    return sum(a.get("alcance_estimado", 0) or 0 for a in articulos)
