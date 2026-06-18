"""Executive report endpoints — PDF is the ONLY export format.

List archived reports, generate a new daily PDF (requires analista+), and
download the binary PDF. Generation works from the demo dataset when the DB is
unavailable, so it never hard-fails.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, Response

from app.core import audit, demo_data, security
from app.schemas import ReporteGenerar
from app.services import pdf_report

router = APIRouter()


@router.get("")
async def listar():
    """List archived reports available for download (PDF only)."""
    return {"items": demo_data.REPORTES}


@router.post("/generar", status_code=201)
async def generar(body: ReporteGenerar, user: dict = Depends(security.require_role("analista"))):
    """Generate the executive report PDF now and store it."""
    meta = pdf_report.generate_and_store()
    await audit.log("generar_reporte", usuario_id=user.get("sub"), entidad="reportes",
                    metadatos={"tipo": body.tipo, "bytes": meta["archivo_bytes"]})
    return meta


@router.get("/{reporte_id}")
async def detalle(reporte_id: str):
    for r in demo_data.REPORTES:
        if r["id"] == reporte_id:
            return r
    return {"id": reporte_id, "estado": "completado", "tipo": "ejecutivo_diario"}


@router.get("/{reporte_id}/pdf")
async def descargar(reporte_id: str):
    """Return the PDF binary. Generates on demand if not yet on disk."""
    # If a stored file exists for today, serve it; otherwise build one now.
    meta = pdf_report.generate_and_store()
    path = meta["archivo_path"]
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf",
                            filename=os.path.basename(path))
    pdf = pdf_report.build_pdf()
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=informe_ejecutivo.pdf"})
