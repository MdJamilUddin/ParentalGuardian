import json
import logging

from app.logging_config import JsonFormatter
from app.main import app
from app.models.db import get_db


def test_liveness(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_readiness_ok(client):
    r = client.get("/health/ready")
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_readiness_fails_when_database_is_down(client):
    class Broken:
        def execute(self, *a, **k):
            raise RuntimeError("db down")

    def broken_db():
        yield Broken()

    app.dependency_overrides[get_db] = broken_db
    try:
        assert client.get("/health/ready").status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_every_response_has_a_request_id(client):
    r = client.get("/children")  # 401/403 is fine, the header must still be there
    assert len(r.headers["x-request-id"]) == 12


def test_json_log_format():
    record = logging.LogRecord("app.access", logging.INFO, __file__, 1, "GET %s %s", ("/x", 200), None)
    record.request_id = "abc"
    data = json.loads(JsonFormatter().format(record))
    assert data["message"] == "GET /x 200" and data["request_id"] == "abc" and data["level"] == "INFO"


def test_root_points_to_the_docs(client):
    r = client.get("/")
    assert r.status_code == 200 and r.json()["docs"] == "/docs"


def _preflight(client, origin):
    return client.options("/auth/login", headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                                                  "Access-Control-Request-Headers": "content-type"})


def test_local_dashboards_may_call_the_api_outside_production(client):
    for origin in ("http://localhost:5173", "http://127.0.0.1:5500"):
        assert _preflight(client, origin).headers["access-control-allow-origin"] == origin


def test_other_websites_are_blocked(client):
    r = _preflight(client, "https://evil.example.org")
    assert "access-control-allow-origin" not in r.headers
