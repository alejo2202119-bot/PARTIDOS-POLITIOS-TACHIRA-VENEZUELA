"""Daily Executive Report PDF generator (reportlab).

Produces an institutional PDF with: cover, generation date, executive summary,
KPIs, day trends, most-mentioned actors, predominant narratives, territorial
analysis, relevant alerts, an evolution chart, and AI/auto-generated
conclusions & recommendations. PDF is the ONLY export format in the system.

Designed to work from the in-memory demo dataset when the DB is unavailable, so
report generation never hard-fails.
"""

from __future__ import annotations

import hashlib
import io
import os
from datetime import date, datetime

from app.config import settings
from app.core import demo_data


# ─────────────────────────── Evolution chart ───────────────────────────────
def _evolution_png(series: list[dict]) -> bytes | None:
    """Render a small multi-series line chart to PNG bytes (matplotlib)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(7.2, 2.6), dpi=150)
        for s in series[:4]:
            ys = [p["y"] for p in s["data"]]
            ax.plot(range(len(ys)), ys, label=s["name"], linewidth=1.8)
        ax.legend(loc="upper left", fontsize=7, frameon=False, ncol=4)
        ax.set_title("Evolución de la cobertura por tema", fontsize=9, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=7)
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        return None


# ─────────────────────────── Auto conclusions ──────────────────────────────
def _conclusions(kpis: dict) -> list[str]:
    s = kpis.get("sentimiento_global", 0)
    tono = "crítico" if s < -0.05 else "equilibrado" if s < 0.1 else "favorable"
    return [
        "La conversación pública mantiene foco en procesos electorales y unidad política; "
        "se recomienda monitorear su evolución en los próximos días.",
        f"El sentimiento global del período es {tono} ({s:+.2f}); conviene atender los temas "
        "de servicios públicos y economía en la región andina.",
        "Priorizar la verificación de narrativas emergentes y contrastar fuentes de distinta credibilidad.",
        "Análisis basado exclusivamente en información pública; las cifras de demostración son sintéticas.",
    ]


# ─────────────────────────── Builder ───────────────────────────────────────
def build_pdf(
    kpis: dict | None = None,
    actores: list[dict] | None = None,
    narrativas: list[dict] | None = None,
    alertas: list[dict] | None = None,
    territorial: list[dict] | None = None,
    series: list[dict] | None = None,
    periodo: tuple[date, date] | None = None,
) -> bytes:
    """Build the executive report PDF and return its bytes."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    kpis = kpis or demo_data.KPIS
    actores = actores or demo_data.ACTORES[:8]
    narrativas = narrativas or demo_data.NARRATIVAS[:5]
    alertas = alertas or demo_data.ALERTAS[:5]
    territorial = territorial or sorted(demo_data.ESTADOS, key=lambda e: e["articulos"], reverse=True)[:8]
    series = series or demo_data.TENDENCIAS["series"]

    now = datetime.now()
    styles = getSampleStyleSheet()
    accent = colors.HexColor("#4338ca")
    muted = colors.HexColor("#64748b")

    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=accent, fontSize=13, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=14)
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, textColor=muted)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        title="Informe Ejecutivo VPID", author=settings.REPORT_BRAND_NAME,
    )
    story: list = []

    # ── Cover band ──────────────────────────────────────────────────────────
    cover = Table(
        [[Paragraph(
            f'<font color="white" size="9">VENEZUELA POLITICAL INTELLIGENCE</font><br/>'
            f'<font color="white" size="22"><b>Informe Ejecutivo Diario</b></font><br/>'
            f'<font color="#c7d2fe" size="9">Monitoreo y análisis de información pública (OSINT)</font><br/><br/>'
            f'<font color="#e0e7ff" size="9">Generado: {now.strftime("%d/%m/%Y %H:%M")}</font>',
            styles["BodyText"])]],
        colWidths=[doc.width],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1e1b4b")),
        ("LEFTPADDING", (0, 0), (-1, -1), 22), ("TOPPADDING", (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22), ("ROUNDEDCORNERS", [8, 8, 8, 8]),
    ]))
    story += [cover, Spacer(1, 14)]

    # ── Executive summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Resumen Ejecutivo", h2))
    story.append(Paragraph(
        f"Durante el período analizado se procesaron <b>{kpis['total_articulos']:,}</b> artículos de "
        f"<b>{kpis['fuentes_activas']}</b> fuentes públicas activas, con <b>{kpis['total_menciones']:,}</b> "
        f"menciones. El sentimiento global se ubicó en <b>{kpis['sentimiento_global']:+.2f}</b> y el alcance "
        f"estimado acumulado alcanzó <b>{kpis['alcance_total']:,}</b>. Se identificaron "
        f"<b>{kpis['narrativas_activas']}</b> narrativas activas "
        f"({kpis['narrativas_emergentes']} emergentes) y <b>{kpis['alertas_abiertas']}</b> alertas abiertas.",
        body,
    ))

    # ── KPIs table ────────────────────────────────────────────────────────────
    story.append(Paragraph("Indicadores Clave", h2))
    kpi_row = [
        ["Artículos", "Menciones", "Alcance", "Sentimiento", "Alertas"],
        [f"{kpis['total_articulos']:,}", f"{kpis['total_menciones']:,}",
         f"{kpis['alcance_total']:,}", f"{kpis['sentimiento_global']:+.2f}",
         str(kpis["alertas_abiertas"])],
    ]
    kt = Table(kpi_row, colWidths=[doc.width / 5] * 5)
    kt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), muted), ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, 1), 14), ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7), ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story += [kt, Spacer(1, 6)]

    # ── Evolution chart ───────────────────────────────────────────────────────
    png = _evolution_png(series)
    if png:
        story += [Spacer(1, 4), Image(io.BytesIO(png), width=doc.width, height=doc.width * 0.36)]

    # ── Most mentioned actors ─────────────────────────────────────────────────
    story.append(Paragraph("Actores Más Mencionados", h2))
    arows = [["Actor", "Cargo", "Menciones", "Sentimiento"]]
    for a in actores[:8]:
        arows.append([a["nombre"], a.get("cargo", ""), f"{a['menciones']:,}", f"{a['sentimiento_prom']:+.2f}"])
    at = Table(arows, colWidths=[doc.width * 0.34, doc.width * 0.30, doc.width * 0.18, doc.width * 0.18])
    at.setStyle(_table_style(accent, muted))
    story.append(at)

    # ── Predominant narratives ────────────────────────────────────────────────
    story.append(Paragraph("Narrativas Predominantes", h2))
    for n in narrativas[:5]:
        tag = " · <font color='#6366f1'>emergente</font>" if n.get("emergente") else ""
        story.append(Paragraph(f"• <b>{n['titulo']}</b> — {n['total_articulos']} artículos{tag}", body))

    # ── Territorial analysis ──────────────────────────────────────────────────
    story.append(Paragraph("Análisis Territorial", h2))
    trows = [["Estado", "Artículos", "Sentimiento"]]
    for t in territorial[:8]:
        trows.append([t["estado"], f"{t['articulos']:,}", f"{t.get('sentimiento_prom', 0):+.2f}"])
    tt = Table(trows, colWidths=[doc.width * 0.5, doc.width * 0.25, doc.width * 0.25])
    tt.setStyle(_table_style(accent, muted))
    story.append(tt)

    # ── Relevant alerts ───────────────────────────────────────────────────────
    story.append(Paragraph("Alertas Relevantes", h2))
    for a in alertas[:5]:
        story.append(Paragraph(f"• <b>[{a['severidad']}]</b> {a['titulo']} — {a['descripcion']}", body))

    # ── Conclusions & recommendations ─────────────────────────────────────────
    story.append(Paragraph("Conclusiones y Recomendaciones (generadas automáticamente)", h2))
    for c in _conclusions(kpis):
        story.append(Paragraph(f"• {c}", body))

    story += [Spacer(1, 16), Paragraph(
        "Documento generado por Venezuela Political Intelligence Dashboard · Exportación únicamente en PDF · "
        "Uso responsable de fuentes abiertas. Esta herramienta no debe emplearse para vigilancia de personas privadas.",
        small,
    )]

    doc.build(story)
    return buf.getvalue()


def _table_style(accent, muted):
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle

    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, 0), muted), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbff")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def generate_and_store(periodo: tuple[date, date] | None = None) -> dict:
    """Build the PDF, persist it to ``REPORTS_STORAGE_PATH`` and return metadata."""
    pdf = build_pdf(periodo=periodo)
    os.makedirs(settings.REPORTS_STORAGE_PATH, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    filename = f"informe_ejecutivo_{stamp}.pdf"
    path = os.path.join(settings.REPORTS_STORAGE_PATH, filename)
    with open(path, "wb") as fh:
        fh.write(pdf)
    return {
        "titulo": f"Informe Ejecutivo Diario — {datetime.now().strftime('%d/%m/%Y')}",
        "tipo": "ejecutivo_diario",
        "estado": "completado",
        "archivo_path": path,
        "archivo_bytes": len(pdf),
        "pdf_sha256": hashlib.sha256(pdf).hexdigest(),
        "completado_en": datetime.now().isoformat(),
    }
