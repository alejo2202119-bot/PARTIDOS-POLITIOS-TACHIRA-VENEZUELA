"""Async Redis cache with graceful degradation.

If Redis is unavailable the cache transparently becomes a no-op, so endpoints
keep working. Provides ``get``/``set`` JSON helpers and a ``@cached`` decorator.
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, Awaitable, Callable

from app.config import settings

logger = logging.getLogger("vpid.cache")

_client: Any = None
_unavailable = False


async def _get_client():
    global _client, _unavailable
    if _unavailable:
        return None
    if _client is None:
        try:
            import redis.asyncio as redis  # local import keeps startup light

            _client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await _client.ping()
            logger.info("Redis cache connected")
        except Exception as exc:  # pragma: no cover - depends on live Redis
            logger.warning("Redis unavailable, caching disabled: %s", exc)
            _unavailable = True
            _client = None
    return _client


async def get(key: str) -> Any | None:
    client = await _get_client()
    if not client:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def set(key: str, value: Any, ttl: int | None = None) -> None:
    client = await _get_client()
    if not client:
        return
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl or settings.CACHE_TTL_SECONDS)
    except Exception:
        pass


def cached(ttl: int | None = None, key: str | None = None):
    """Decorator caching an async function's JSON-serializable result."""

    def deco(fn: Callable[..., Awaitable[Any]]):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            cache_key = key or f"vpid:{fn.__module__}.{fn.__name__}"
            hit = await get(cache_key)
            if hit is not None:
                return hit
            result = await fn(*args, **kwargs)
            await set(cache_key, result, ttl)
            return result

        return wrapper

    return deco


async def ping() -> bool:
    return (await _get_client()) is not None
