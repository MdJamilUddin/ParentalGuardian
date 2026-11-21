from util import iso, today


def sync(client, p, **payload):
    return client.post("/device/sync", json=payload, headers=p.device)


def test_sync_then_parent_reads_everything(client, paired):
    p = paired()
    r = sync(
        client, p,
        locations=[
            {"lat": 23.80, "lng": 90.40, "accuracy_m": 20, "recorded_at": iso(30)},
            {"lat": 23.81, "lng": 90.41, "accuracy_m": 15, "recorded_at": iso(5)},
        ],
        battery=[{"level": 64, "charging": True, "recorded_at": iso(1)}],
        usage=[{"package": "com.example.game", "app_label": "Game", "day": today(), "seconds": 1800}],
    )
    assert r.status_code == 200
    assert r.json()["accepted_locations"] == 2

    latest = client.get(f"/children/{p.child_id}/location/latest", headers=p.parent).json()
    assert latest["lat"] == 23.81  # newest point wins

    history = client.get(f"/children/{p.child_id}/locations?hours=24", headers=p.parent).json()
    assert len(history) == 2 and history[0]["lat"] == 23.81  # newest first

    battery = client.get(f"/children/{p.child_id}/battery", headers=p.parent).json()
    assert battery["level"] == 64 and battery["charging"] is True

    usage = client.get(f"/children/{p.child_id}/usage?day={today()}", headers=p.parent).json()
    assert usage[0]["package"] == "com.example.game" and usage[0]["seconds"] == 1800


def test_history_respects_hours_window(client, paired):
    p = paired()
    sync(client, p, locations=[
        {"lat": 1.0, "lng": 1.0, "recorded_at": iso(60 * 5)},
        {"lat": 2.0, "lng": 2.0, "recorded_at": iso(10)},
    ])
    recent = client.get(f"/children/{p.child_id}/locations?hours=1", headers=p.parent).json()
    assert [x["lat"] for x in recent] == [2.0]


def test_usage_is_last_value_wins(client, paired):
    p = paired()
    entry = {"package": "com.example.app", "app_label": "App", "day": today()}
    sync(client, p, usage=[{**entry, "seconds": 600}])
    sync(client, p, usage=[{**entry, "seconds": 900}])
    usage = client.get(f"/children/{p.child_id}/usage?day={today()}", headers=p.parent).json()
    assert len(usage) == 1 and usage[0]["seconds"] == 900


def test_empty_state_returns_null_and_empty_lists(client, paired):
    p = paired()
    assert client.get(f"/children/{p.child_id}/location/latest", headers=p.parent).json() is None
    assert client.get(f"/children/{p.child_id}/battery", headers=p.parent).json() is None
    assert client.get(f"/children/{p.child_id}/usage?day={today()}", headers=p.parent).json() == []


def test_invalid_data_rejected(client, paired):
    p = paired()
    assert sync(client, p, locations=[{"lat": 95, "lng": 0, "recorded_at": iso()}]).status_code == 422
    assert sync(client, p, locations=[{"lat": 0, "lng": 181, "recorded_at": iso()}]).status_code == 422
    assert sync(client, p, battery=[{"level": 101, "recorded_at": iso()}]).status_code == 422
    bad_usage = {"package": "p", "day": "21-11-2026", "seconds": 5}
    assert sync(client, p, usage=[bad_usage]).status_code == 422
    too_many = [{"lat": 0, "lng": 0, "recorded_at": iso()}] * 501
    assert sync(client, p, locations=too_many).status_code == 422


def test_revoked_device_is_locked_out_and_hidden(client, paired):
    p = paired()
    sync(client, p, locations=[{"lat": 5.0, "lng": 5.0, "recorded_at": iso()}])
    assert client.delete(f"/devices/{p.device_id}", headers=p.parent).status_code == 204

    assert sync(client, p).status_code == 401  # child app sees 401 and returns to the pairing screen
    assert client.get(f"/children/{p.child_id}/location/latest", headers=p.parent).json() is None
