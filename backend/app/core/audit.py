"""Best-effort audit logging into the ``auditoria`` table.

Never raises: auditing must not break the request it records. When the DB is
unavailable the event is logged to the application logger instead.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("vpid.audit")


async def log(
    accion: str,
    *,
    usuario_id: str | None = None,
    entidad: str | None = None,
    entidad_id: str | None = None,
    metadatos: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Record an audit event (DB if reachable, otherwise log)."""
    payload = {
        "accion": accion,
        "usuario_id": usuario_id,
        "entidad": entidad,
        "entidad_id": entidad_id,
        "metadatos": metadatos or {},
        "ip": ip,
        "user_agent": user_agent,
    }
    try:
        from sqlalchemy import text

        from app.database import get_sessionmaker, ping

        if not await ping():
            raise RuntimeError("db-unreachable")

        async with get_sessionmaker()() as session:
            await session.execute(
                text(
                    "INSERT INTO auditoria (usuario_id, accion, entidad, entidad_id, metadatos, ip, user_agent) "
                    "VALUES (CAST(:usuario_id AS uuid), :accion, :entidad, :entidad_id, CAST(:metadatos AS jsonb), "
                    "CAST(:ip AS inet), :user_agent)"
                ),
                {
                    **payload,
                    "metadatos": __import__("json").dumps(payload["metadatos"]),
                    "usuario_id": usuario_id if usuario_id and usuario_id != "demo" else None,
                },
            )
            await session.commit()
    except Exception as exc:  # pragma: no cover - depends on live DB
        logger.info("AUDIT %s entidad=%s id=%s (db skipped: %s)", accion, entidad, entidad_id, exc)
