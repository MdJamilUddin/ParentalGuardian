from datetime import timedelta

from app.models.db import SessionLocal
from app.models.entities import Device, PushToken, utcnow
from app.services.alerts import check_stale_devices
from util import bearer, iso

TOKEN_A = "fcm-token-phone-one-0123456789"
TOKEN_B = "fcm-token-phone-two-9876543210"


def register_push(client, parent, token=TOKEN_A):
    r = client.put("/me/push-token", json={"token": token}, headers=parent)
    assert r.status_code == 204, r.text


def battery(level, charging=False, minutes_ago=0):
    return {"battery": [{"level": level, "charging": charging, "recorded_at": iso(minutes_ago)}]}


def sync(client, p, **payload):
    return client.post("/device/sync", json=payload, headers=p.device)


# ---- token registration and preferences
def test_token_moves_to_the_latest_account(client, register):
    a, b = register("a@example.com"), register("b@example.com")
    register_push(client, a)
    register_push(client, b)  # same phone, other account
    with SessionLocal() as db:
        assert db.query(PushToken).count() == 1
    assert client.get("/me/notifications", headers=a).json()["devices"] == 0
    assert client.get("/me/notifications", headers=b).json()["devices"] == 1


def test_unregister_only_removes_own_token(client, register):
    a, b = register("a@example.com"), register("b@example.com")
    register_push(client, a)
    client.post("/me/push-token/unregister", json={"token": TOKEN_A}, headers=b)
    assert client.get("/me/notifications", headers=a).json()["devices"] == 1
    client.post("/me/push-token/unregister", json={"token": TOKEN_A}, headers=a)
    assert client.get("/me/notifications", headers=a).json()["devices"] == 0


def test_preferences_default_on_and_can_change(client, register):
    a = register()
    assert client.get("/me/notifications", headers=a).json() == {"offline": True, "low_battery": True, "devices": 0}
    r = client.put("/me/notifications", json={"offline": False, "low_battery": True}, headers=a)
    assert r.json()["offline"] is False


def test_notification_routes_need_a_parent_login(client, paired):
    p = paired()
    assert client.get("/me/notifications", headers=p.device).status_code == 401


def test_test_notification(client, register, sender):
    a = register()
    assert client.post("/me/push-test", headers=a).json() == {"sent": 0, "registered": 0, "configured": True}
    register_push(client, a)
    r = client.post("/me/push-test", headers=a).json()
    assert r["sent"] == 1 and sender.calls[0]["tokens"] == [TOKEN_A]


def test_dead_tokens_are_removed(client, register, sender):
    a = register()
    register_push(client, a)
    sender.invalid = [TOKEN_A]
    assert client.post("/me/push-test", headers=a).json()["sent"] == 0
    assert client.get("/me/notifications", headers=a).json()["devices"] == 0


# ---- low battery
def test_low_battery_alerts_once_and_rearms(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    sync(client, p, **battery(40))
    assert sender.calls == []
    sync(client, p, **battery(12))
    assert len(sender.calls) == 1 and sender.calls[0]["data"]["type"] == "low_battery"
    assert sender.calls[0]["data"]["child_id"] == str(p.child_id) or sender.calls[0]["data"]["child_id"] == p.child_id
    sync(client, p, **battery(9))
    assert len(sender.calls) == 1  # still the same low period
    sync(client, p, **battery(55))  # recovered
    sync(client, p, **battery(14))
    assert len(sender.calls) == 2


def test_charging_phone_does_not_alert(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    sync(client, p, **battery(5, charging=True))
    assert sender.calls == []


def test_old_queued_reading_does_not_alert(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    sync(client, p, **battery(5, minutes_ago=180))
    assert sender.calls == []


def test_low_battery_alert_can_be_switched_off(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    client.put("/me/notifications", json={"offline": True, "low_battery": False}, headers=p.parent)
    sync(client, p, **battery(5))
    assert sender.calls == []


# ---- phone stopped reporting
def make_stale(device_id, hours=3):
    with SessionLocal() as db:
        db.query(Device).filter(Device.id == device_id).update({"last_seen": utcnow() - timedelta(hours=hours)})
        db.commit()


def test_offline_alert_once_per_outage(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    make_stale(p.device_id)
    with SessionLocal() as db:
        assert check_stale_devices(db) == 1
    assert sender.calls[0]["data"]["type"] == "offline" and "3 h" in sender.calls[0]["body"]
    with SessionLocal() as db:
        assert check_stale_devices(db) == 0  # same outage, no repeat

    assert sync(client, p).status_code == 200  # the phone comes back
    with SessionLocal() as db:
        assert check_stale_devices(db) == 0
        assert check_stale_devices(db, now=utcnow() + timedelta(hours=3)) == 1  # a new outage
    assert len(sender.calls) == 2


def test_recent_and_revoked_devices_are_ignored(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    sync(client, p)  # just seen
    with SessionLocal() as db:
        assert check_stale_devices(db) == 0
    make_stale(p.device_id)
    client.delete(f"/devices/{p.device_id}", headers=p.parent)
    with SessionLocal() as db:
        assert check_stale_devices(db) == 0
    assert sender.calls == []


def test_paired_but_never_synced_phone(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    with SessionLocal() as db:
        db.query(Device).update({"paired_at": utcnow() - timedelta(hours=5), "last_seen": None})
        db.commit()
        assert check_stale_devices(db) == 1
    assert "not sent any data" in sender.calls[0]["body"]


def test_offline_alert_respects_preference(client, paired, sender):
    p = paired()
    register_push(client, p.parent)
    client.put("/me/notifications", json={"offline": False, "low_battery": True}, headers=p.parent)
    make_stale(p.device_id)
    with SessionLocal() as db:
        assert check_stale_devices(db) == 0
    assert sender.calls == []


# ---- scheduler endpoint
def test_cron_endpoint(client, paired, sender, monkeypatch):
    from app.config.settings import settings
    assert client.post("/internal/check-alerts").status_code == 404  # disabled by default
    monkeypatch.setattr(settings, "CRON_SECRET", "s3cret-value")
    assert client.post("/internal/check-alerts").status_code == 401
    assert client.post("/internal/check-alerts", headers={"X-Cron-Secret": "nope"}).status_code == 401
    p = paired()
    register_push(client, p.parent)
    make_stale(p.device_id)
    r = client.post("/internal/check-alerts", headers={"X-Cron-Secret": "s3cret-value"})
    assert r.status_code == 200 and r.json() == {"offline_alerts": 1}
