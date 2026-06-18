"""Sentiment analysis endpoints + ad-hoc text scoring."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core import demo_data
from app.services import sentiment as svc

router = APIRouter()


class TextoIn(BaseModel):
    texto: str


@router.get("/resumen")
async def resumen():
    """Sentiment distribution + global score and per-topic series."""
    return demo_data.SENTIMIENTO


@router.get("/series")
async def series():
    """Per-topic sentiment time-series."""
    return {"series": demo_data.SENTIMIENTO["series"]}


@router.post("/analizar")
async def analizar(body: TextoIn):
    """Score an arbitrary public text (uses the configured AI/lexicon provider)."""
    result = await svc.analyze(body.texto)
    return result.model_dump()
