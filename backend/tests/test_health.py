"""Health & root endpoint tests."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "db" in body and "cache" in body


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "PDF" in r.json()["note"]


def test_openapi(client):
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()
