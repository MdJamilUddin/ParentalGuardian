from app.models.db import SessionLocal
from app.models.entities import (BatteryReading, Child, Device, LocationPoint, Parent, Place, PushToken,
                                 UsageRecord)
from util import iso, today

NEW = {"email": "new@example.com", "name": "New", "password": "password123"}


def test_registration_requires_accepting_the_terms(client):
    assert client.post("/auth/register", json=NEW).status_code == 422
    assert client.post("/auth/register", json={**NEW, "accepted_terms": False}).status_code == 422
    assert client.post("/auth/register", json={**NEW, "accepted_terms": True}).status_code == 201
    with SessionLocal() as db:
        parent = db.query(Parent).one()
        assert parent.terms_accepted_at is not None and parent.terms_version


def fill_account(client, p):
    client.post("/device/sync", headers=p.device, json={
        "locations": [{"lat": 23.8, "lng": 90.4, "recorded_at": iso()}],
        "battery": [{"level": 50, "charging": False, "recorded_at": iso()}],
        "usage": [{"package": "com.example", "day": today(), "seconds": 60}],
    })
    client.post(f"/children/{p.child_id}/places", headers=p.parent, json={"name": "Home", "lat": 23.8, "lng": 90.4})
    client.put("/me/push-token", headers=p.parent, json={"token": "fcm-token-delete-test-0123456789"})


def test_wrong_password_does_not_delete(client, paired):
    p = paired()
    assert client.post("/me/delete", json={"password": "nope-nope-nope"}, headers=p.parent).status_code == 403
    assert client.get("/children", headers=p.parent).status_code == 200


def test_delete_account_removes_everything(client, paired):
    p = paired("a@example.com")
    other = paired("b@example.com", "Other kid")
    fill_account(client, p)
    fill_account(client, other)

    assert client.post("/me/delete", json={"password": "correct-horse-1"}, headers=p.parent).status_code == 204

    # the old login and the phone's token stop working
    assert client.post("/auth/login", json={"email": "a@example.com", "password": "correct-horse-1"}).status_code == 401
    assert client.get("/children", headers=p.parent).status_code == 401
    assert client.post("/device/sync", json={}, headers=p.device).status_code == 401

    with SessionLocal() as db:
        # only the other parent's data is left, one of everything
        for model in (Parent, Child, Device, LocationPoint, BatteryReading, UsageRecord, Place, PushToken):
            assert db.query(model).count() == 1, model.__name__
    assert client.get("/children", headers=other.parent).status_code == 200


def test_export_contains_the_parents_data(client, paired):
    p = paired()
    fill_account(client, p)
    data = client.get("/me/export", headers=p.parent).json()
    assert data["account"]["email"] == "parent1@example.com"
    child = data["children"][0]
    assert child["name"] == "Kid" and len(child["locations"]) == 1 and child["places"][0]["name"] == "Home"
    assert child["app_usage"][0]["package"] == "com.example"


def test_export_needs_a_login(client):
    assert client.get("/me/export").status_code in (401, 403)
