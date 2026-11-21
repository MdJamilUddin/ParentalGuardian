"""A parent must never reach another parent's child or device."""
from util import today


def test_children_list_only_shows_own(client, paired, register):
    paired("a@example.com", "A-kid")
    other = register("b@example.com")
    assert client.get("/children", headers=other).json() == []


def test_other_parent_gets_404_everywhere(client, paired, register):
    a = paired("a@example.com")
    b = register("b@example.com")
    cid = a.child_id
    assert client.post(f"/children/{cid}/pairing-code", headers=b).status_code == 404
    assert client.get(f"/children/{cid}/location/latest", headers=b).status_code == 404
    assert client.get(f"/children/{cid}/locations", headers=b).status_code == 404
    assert client.get(f"/children/{cid}/usage?day={today()}", headers=b).status_code == 404
    assert client.get(f"/children/{cid}/battery", headers=b).status_code == 404


def test_other_parent_cannot_revoke_device(client, paired, register):
    a = paired("a@example.com")
    b = register("b@example.com")
    assert client.delete(f"/devices/{a.device_id}", headers=b).status_code == 404
    # the device still works
    r = client.post("/device/sync", json={}, headers=a.device)
    assert r.status_code == 200


def test_device_token_is_not_a_parent_login(client, paired):
    a = paired()
    assert client.get("/children", headers=a.device).status_code == 401


def test_parent_token_cannot_sync(client, paired):
    a = paired()
    assert client.post("/device/sync", json={}, headers=a.parent).status_code == 401
