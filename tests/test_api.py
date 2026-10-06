import pytest
from fastapi.testclient import TestClient

from app.cache import Cache
from app.main import create_app
from app.storage import MemoryStore


@pytest.fixture()
def client():
    with TestClient(create_app(MemoryStore(), Cache(None))) as c:
        yield c


def test_health(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200


def test_create_redirect_and_stats(client):
    r = client.post("/api/v1/links", json={"url": "https://example.com/page"})
    assert r.status_code == 201
    code = r.json()["code"]
    assert len(code) == 7

    redirect = client.get(f"/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/page"

    stats = client.get(f"/api/v1/links/{code}/stats").json()
    assert stats["hits"] == 1


def test_invalid_url_rejected(client):
    assert client.post("/api/v1/links", json={"url": "not-a-url"}).status_code == 422


def test_unknown_code_404(client):
    assert client.get("/doesnotexist", follow_redirects=False).status_code == 404


def test_metrics_exposed(client):
    client.get("/healthz")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
    assert "links_created_total" in body
