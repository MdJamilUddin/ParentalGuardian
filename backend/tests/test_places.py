from app.services.places import distance_m
from util import iso

HOME = (23.8000, 90.4000)
INSIDE = HOME
NEAR_EDGE = (23.80099, 90.4000)   # about 110 m away: outside a 100 m circle, inside the exit buffer
OUTSIDE = (23.8100, 90.4000)      # about 1.1 km away
TOKEN = "fcm-token-parent-places-0123456789"


def add_place(client, p, name="Home", radius=100, at=HOME):
    r = client.post(f"/children/{p.child_id}/places",
                    json={"name": name, "lat": at[0], "lng": at[1], "radius_m": radius}, headers=p.parent)
    assert r.status_code == 201, r.text
    return r.json()


def loc(at, minutes_ago=0, accuracy=20):
    return {"lat": at[0], "lng": at[1], "accuracy_m": accuracy, "recorded_at": iso(minutes_ago)}


def sync(client, p, *points):
    r = client.post("/device/sync", json={"locations": list(points)}, headers=p.device)
    assert r.status_code == 200, r.text


def places(client, p):
    return client.get(f"/children/{p.child_id}/places", headers=p.parent).json()


def with_push(client, p):
    client.put("/me/push-token", json={"token": TOKEN}, headers=p.parent)


def test_distance():
    assert abs(distance_m(23.8, 90.4, 23.801, 90.4) - 111.2) < 1.5
    assert distance_m(23.8, 90.4, 23.8, 90.4) == 0


def test_create_list_delete(client, paired):
    p = paired()
    place = add_place(client, p, "School", 200)
    assert place["inside"] is None and place["radius_m"] == 200
    assert [x["name"] for x in places(client, p)] == ["School"]
    assert client.delete(f"/places/{place['id']}", headers=p.parent).status_code == 204
    assert places(client, p) == []


def test_validation(client, paired):
    p = paired()
    url = f"/children/{p.child_id}/places"
    ok = {"name": "X", "lat": 23.8, "lng": 90.4, "radius_m": 100}
    assert client.post(url, json={**ok, "radius_m": 10}, headers=p.parent).status_code == 422
    assert client.post(url, json={**ok, "radius_m": 5000}, headers=p.parent).status_code == 422
    assert client.post(url, json={**ok, "lat": 95}, headers=p.parent).status_code == 422
    assert client.post(url, json={**ok, "name": ""}, headers=p.parent).status_code == 422


def test_at_most_ten_places(client, paired):
    p = paired()
    for i in range(10):
        add_place(client, p, f"P{i}")
    r = client.post(f"/children/{p.child_id}/places", json={"name": "11", "lat": 1, "lng": 1}, headers=p.parent)
    assert r.status_code == 400


def test_other_parent_has_no_access(client, paired, register):
    p = paired("a@example.com")
    place = add_place(client, p)
    other = register("b@example.com")
    assert client.get(f"/children/{p.child_id}/places", headers=other).status_code == 404
    assert client.post(f"/children/{p.child_id}/places", json={"name": "X", "lat": 1, "lng": 1}, headers=other).status_code == 404
    assert client.delete(f"/places/{place['id']}", headers=other).status_code == 404


def test_arrive_then_leave(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p, "Home", 100)

    sync(client, p, loc(OUTSIDE))                      # first reading: silent
    assert sender.calls == [] and places(client, p)[0]["inside"] is False

    sync(client, p, loc(INSIDE))
    assert len(sender.calls) == 1
    assert sender.calls[0]["data"]["type"] == "place_arrived" and "Home" in sender.calls[0]["title"]

    sync(client, p, loc(INSIDE))                       # still there: no repeat
    sync(client, p, loc(NEAR_EDGE))                    # GPS drift just outside the circle: still "inside"
    assert len(sender.calls) == 1 and places(client, p)[0]["inside"] is True

    sync(client, p, loc(OUTSIDE))
    assert len(sender.calls) == 2 and sender.calls[1]["data"]["type"] == "place_left"


def test_first_reading_is_silent(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p)
    sync(client, p, loc(INSIDE))
    assert sender.calls == [] and places(client, p)[0]["inside"] is True


def test_new_place_learns_state_from_latest_location(client, paired, sender):
    p = paired()
    with_push(client, p)
    sync(client, p, loc(INSIDE))
    add_place(client, p)
    assert places(client, p)[0]["inside"] is True
    sync(client, p, loc(OUTSIDE))
    assert [c["data"]["type"] for c in sender.calls] == ["place_left"]


def test_old_readings_update_state_without_alert(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p)
    sync(client, p, loc(OUTSIDE))
    sync(client, p, loc(INSIDE, minutes_ago=180))     # the phone was offline, this is old news
    assert sender.calls == [] and places(client, p)[0]["inside"] is True


def test_imprecise_fixes_are_ignored(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p)
    sync(client, p, loc(OUTSIDE))
    sync(client, p, loc(INSIDE, accuracy=500))
    assert sender.calls == [] and places(client, p)[0]["inside"] is False


def test_in_and_out_within_one_batch_is_not_news(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p)
    sync(client, p, loc(OUTSIDE))
    sync(client, p, loc(INSIDE, minutes_ago=10), loc(OUTSIDE, minutes_ago=5))
    assert sender.calls == []


def test_place_alerts_can_be_switched_off(client, paired, sender):
    p = paired()
    with_push(client, p)
    add_place(client, p)
    client.put("/me/notifications", json={"offline": True, "low_battery": True, "places": False}, headers=p.parent)
    sync(client, p, loc(OUTSIDE))
    sync(client, p, loc(INSIDE))
    assert sender.calls == [] and places(client, p)[0]["inside"] is True


def test_older_apps_cannot_reset_the_places_setting(client, register):
    a = register()
    client.put("/me/notifications", json={"offline": True, "low_battery": True, "places": False}, headers=a)
    client.put("/me/notifications", json={"offline": False, "low_battery": True}, headers=a)  # no "places" key
    prefs = client.get("/me/notifications", headers=a).json()
    assert prefs["places"] is False and prefs["offline"] is False
