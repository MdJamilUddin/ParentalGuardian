from util import bearer


def test_register_and_login(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "name": "A", "password": "password123"})
    assert r.status_code == 201 and r.json()["access_token"]
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_email_is_case_insensitive(client):
    client.post("/auth/register", json={"email": "Mixed@Example.com", "name": "A", "password": "password123"})
    r = client.post("/auth/login", json={"email": "mixed@example.com", "password": "password123"})
    assert r.status_code == 200


def test_duplicate_email_rejected(client, register):
    register("dup@example.com")
    r = client.post("/auth/register", json={"email": "dup@example.com", "name": "B", "password": "password123"})
    assert r.status_code == 409


def test_wrong_password_rejected(client, register):
    register("a@example.com", password="password123")
    r = client.post("/auth/login", json={"email": "a@example.com", "password": "not-the-password"})
    assert r.status_code == 401


def test_unknown_email_rejected(client):
    r = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "a@example.com", "name": "A", "password": "short"})
    assert r.status_code == 422


def test_protected_routes_need_a_token(client):
    assert client.get("/children").status_code in (401, 403)
    assert client.get("/children", headers=bearer("garbage.token.value")).status_code == 401


def test_login_is_rate_limited(client, register):
    register("a@example.com", password="password123")
    codes = [client.post("/auth/login", json={"email": "a@example.com", "password": "wrong-password"}).status_code
             for _ in range(11)]
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
