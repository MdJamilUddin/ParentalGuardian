from datetime import timedelta

from app.models.db import SessionLocal
from app.models.entities import Device, PairingCode, utcnow


def test_code_is_six_digits_and_pairs_once(client, register):
    parent = register()
    child = client.post("/children", json={"name": "Kid"}, headers=parent).json()
    code = client.post(f"/children/{child['id']}/pairing-code", headers=parent).json()["code"]
    assert len(code) == 6 and code.isdigit()

    ok = client.post("/device/pair", json={"code": code, "device_name": "Phone"})
    assert ok.status_code == 200 and ok.json()["device_token"]

    again = client.post("/device/pair", json={"code": code, "device_name": "Other phone"})
    assert again.status_code == 400  # single use


def test_wrong_code_rejected(client):
    r = client.post("/device/pair", json={"code": "000000", "device_name": "Phone"})
    assert r.status_code == 400


def test_expired_code_rejected(client, register):
    parent = register()
    child = client.post("/children", json={"name": "Kid"}, headers=parent).json()
    code = client.post(f"/children/{child['id']}/pairing-code", headers=parent).json()["code"]
    with SessionLocal() as db:
        db.query(PairingCode).update({"expires_at": utcnow() - timedelta(minutes=1)})
        db.commit()
    r = client.post("/device/pair", json={"code": code, "device_name": "Phone"})
    assert r.status_code == 400


def test_pairing_attempts_are_rate_limited(client):
    codes = [client.post("/device/pair", json={"code": "123456", "device_name": "Phone"}).status_code
             for _ in range(11)]
    assert codes[:10] == [400] * 10
    assert codes[10] == 429


def test_secrets_are_stored_hashed(paired):
    p = paired()
    with SessionLocal() as db:
        device = db.query(Device).one()
        assert device.token_hash != p.device_token and len(device.token_hash) == 64
        stored_code = db.query(PairingCode).one()
        assert stored_code.code_hash != p.code
