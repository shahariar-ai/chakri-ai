"""Render ডিপ্লয়-সংক্রান্ত কনফিগ: DATABASE_URL normalize, /api/health, CORS, bKash callback URL।"""
from types import SimpleNamespace

import database
from routers import payments


def test_database_url_fallback_is_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database.get_database_url() == database.SQLITE_FALLBACK_URL


def test_database_url_postgres_scheme_normalized(monkeypatch):
    # Render/Heroku-স্টাইল postgres:// -> SQLAlchemy-র postgresql://
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    assert database.get_database_url() == "postgresql://u:p@host:5432/db"
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host/db")
    assert database.get_database_url() == "postgresql://u:p@host/db"


def test_health_reports_db_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["database_engine"] == database.engine.dialect.name
    assert body["ai_configured"] is True


def test_cors_allows_any_origin_without_credentials(client):
    r = client.options(
        "/api/health",
        headers={"Origin": "https://example.com", "Access-Control-Request-Method": "GET"},
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in r.headers


def test_public_base_url_priority(monkeypatch):
    req = SimpleNamespace(base_url="http://10.0.2.2:8000/")
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    assert payments._public_base_url(req) == "http://10.0.2.2:8000"

    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://chakri-ai-backend.onrender.com")
    assert payments._public_base_url(req) == "https://chakri-ai-backend.onrender.com"

    monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.example.com/")
    assert payments._public_base_url(req) == "https://api.example.com"
