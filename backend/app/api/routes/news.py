"""News monitoring endpoints: list & retrieve classified public articles."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core import demo_data

router = APIRouter()


@router.get("")
async def listar(
    q: str | None = None,
    tema: str | None = None,
    estado: str | None = None,
    relevancia: str | None = None,
    sentimiento: str | None = None,
    fuente: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
):
    """Filterable, paginated article list (demo dataset; DB-backed in prod)."""
    items = list(demo_data.ARTICULOS)
    if q:
        ql = q.lower()
        items = [a for a in items if ql in (a["titulo"] + a["actor"] + a["fuente"]).lower()]
    if tema:
        items = [a for a in items if a["tema"] == tema]
    if estado:
        items = [a for a in items if a["estado"] == estado]
    if relevancia:
        items = [a for a in items if a["relevancia"] == relevancia]
    if sentimiento:
        items = [a for a in items if a["sentimiento"] == sentimiento]
    if fuente:
        items = [a for a in items if a["fuente"] == fuente]

    total = len(items)
    start = (page - 1) * size
    return {"items": items[start : start + size], "total": total, "page": page, "size": size}


@router.get("/{articulo_id}")
async def detalle(articulo_id: str):
    for a in demo_data.ARTICULOS:
        if a["id"] == articulo_id:
            return a
    raise HTTPException(status_code=404, detail="Artículo no encontrado")
