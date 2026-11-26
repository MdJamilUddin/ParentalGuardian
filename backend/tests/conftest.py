import os
import tempfile
from types import SimpleNamespace

# Must be set before the app is imported: settings and the database engine are created at import time.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models import entities  # noqa: E402,F401
from app.models.db import Base, engine  # noqa: E402
from app.routes import account as account_routes  # noqa: E402
from app.routes import auth as auth_routes  # noqa: E402
from app.routes import device as device_routes  # noqa: E402
from app.routes import push as push_routes  # noqa: E402
from util import bearer  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_state():
    """Empty database and cleared rate limiters before every test."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    for limiter in (auth_routes.login_limit, auth_routes.register_limit, device_routes.pair_limit, push_routes.test_limit, account_routes.delete_limit):
        limiter.hits.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def register(client):
    def _register(email="parent1@example.com", password="correct-horse-1", name="Parent"):
        r = client.post("/auth/register", json={"email": email, "name": name, "password": password,
                                                    "accepted_terms": True})
        assert r.status_code == 201, r.text
        return bearer(r.json()["access_token"])
    return _register


@pytest.fixture
def paired(client, register):
    """Creates a parent, a child and one paired phone."""
    def _make(email="parent1@example.com", child_name="Kid"):
        parent = register(email)
        child = client.post("/children", json={"name": child_name}, headers=parent).json()
        code = client.post(f"/children/{child['id']}/pairing-code", headers=parent).json()["code"]
        r = client.post("/device/pair", json={"code": code, "device_name": "Test phone"})
        assert r.status_code == 200, r.text
        d = r.json()
        return SimpleNamespace(
            parent=parent, child_id=child["id"], code=code,
            device_id=d["device_id"], device_token=d["device_token"], device=bearer(d["device_token"]),
        )
    return _make


class FakeSender:
    configured = True

    def __init__(self):
        self.calls = []
        self.invalid = []

    def send(self, tokens, title, body, data):
        self.calls.append({"tokens": list(tokens), "title": title, "body": body, "data": data})
        return list(self.invalid)


@pytest.fixture
def sender():
    from app.services import push
    fake = FakeSender()
    push.set_sender(fake)
    yield fake
    push.set_sender(None)
