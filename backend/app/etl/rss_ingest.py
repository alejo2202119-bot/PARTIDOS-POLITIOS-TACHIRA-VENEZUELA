"""Stage 1 — ingest public RSS/Atom feeds.

Fetches each source's feed (httpx + feedparser), deduplicates by a SHA-256 hash
of the normalized URL, and yields raw article dicts. Respects a configurable
robots/ToS flag and a per-source article cap. No private data is collected.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from app.config import settings

logger = logging.getLogger("vpid.etl.ingest")


def url_hash(url: str) -> str:
    """Stable dedupe key: sha256 of the normalized URL (scheme+host+path)."""
    parts = urlsplit(url.strip().lower())
    normalized = urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def fetch_feed(url: str) -> list[dict]:
    """Fetch and parse a single RSS/Atom feed into raw article dicts."""
    import feedparser
    import httpx

    try:
        async with httpx.AsyncClient(
            timeout=settings.ETL_REQUEST_TIMEOUT,
            headers={"User-Agent": settings.ETL_USER_AGENT},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
    except Exception as exc:
        logger.warning("Feed fetch failed for %s: %s", url, exc)
        return []

    out: list[dict] = []
    for entry in parsed.entries[: settings.ETL_MAX_ARTICLES_PER_SOURCE]:
        link = entry.get("link", "")
        if not link:
            continue
        published = None
        if entry.get("published_parsed"):
            try:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            except Exception:
                published = None
        out.append({
            "url": link,
            "url_hash": url_hash(link),
            "titulo": entry.get("title", "(sin título)"),
            "resumen": entry.get("summary", "")[:2000],
            "autor": entry.get("author"),
            "publicado_en": published,
            "estado": "crudo",
        })
    logger.info("Ingested %d items from %s", len(out), url)
    return out


async def run(fuentes: list[dict]) -> list[dict]:
    """Ingest all active sources that expose an RSS URL.

    ``fuentes`` is a list of dicts with at least ``rss_url`` (and ``estado``).
    Returns a deduplicated list of raw article dicts.
    """
    seen: set[str] = set()
    articles: list[dict] = []
    for f in fuentes:
        if f.get("estado") not in (None, "activa"):
            continue
        rss = f.get("rss_url")
        if not rss:
            continue
        if settings.ETL_RESPECT_ROBOTS_TXT and f.get("robots_ok") is False:
            logger.info("Skipping %s (robots/ToS not permitted)", f.get("nombre"))
            continue
        for art in await fetch_feed(rss):
            if art["url_hash"] in seen:
                continue
            seen.add(art["url_hash"])
            art["fuente_id"] = f.get("id")
            articles.append(art)
    return articles
