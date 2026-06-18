"""Every read endpoint returns data via the demo fallback (no DB required)."""

import pytest

READ_ENDPOINTS = [
    "/api/v1/dashboard/kpis",
    "/api/v1/dashboard/overview",
    "/api/v1/articulos",
    "/api/v1/tendencias",
    "/api/v1/tendencias/emergentes",
    "/api/v1/narrativas",
    "/api/v1/sentimiento/resumen",
    "/api/v1/sentimiento/series",
    "/api/v1/actores/ranking",
    "/api/v1/territorial/resumen",
    "/api/v1/alertas",
    "/api/v1/fuentes",
    "/api/v1/reportes",
    "/api/v1/etl/estado",
    "/api/v1/comparativos/correlaciones",
]


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_read_endpoint_ok(client, path):
    r = client.get(path)
    assert r.status_code == 200, path
    assert r.json() is not None


def test_kpis_shape(client):
    body = client.get("/api/v1/dashboard/kpis").json()
    for key in ("total_articulos", "total_menciones", "sentimiento_global", "alcance_total"):
        assert key in body


def test_articulos_filter(client):
    r = client.get("/api/v1/articulos", params={"sentimiento": "negativo", "size": 10})
    body = r.json()
    assert "items" in body and "total" in body
    assert all(a["sentimiento"] == "negativo" for a in body["items"])


def test_search(client):
    r = client.get("/api/v1/buscar", params={"q": "ma"})
    assert r.status_code == 200
    assert "items" in r.json()


def test_login_demo(client):
    r = client.post("/api/v1/auth/login", json={"email": "admin@vpid.local", "password": "x"})
    assert r.status_code == 200
    assert r.json()["access_token"]
