"""Local lexicon sentiment scorer tests."""

from app.services.sentiment import analyze_local


def test_positive():
    r = analyze_local("Gran avance y acuerdo de unidad genera esperanza y progreso")
    assert r.etiqueta == "positivo"
    assert r.score > 0


def test_negative():
    r = analyze_local("Denuncian represión, censura y crisis con violencia y corrupción")
    assert r.etiqueta == "negativo"
    assert r.score < 0


def test_neutral_empty():
    r = analyze_local("")
    assert r.etiqueta == "neutral"
    assert r.score == 0.0


def test_score_bounds():
    r = analyze_local("acuerdo crisis avance represión")
    assert -1.0 <= r.score <= 1.0
    assert 0.0 <= r.confianza <= 1.0
