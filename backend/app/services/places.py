import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..models.entities import Child, Place, utcnow

MAX_ACCURACY_M = 150          # ignore fixes less precise than this (indoor / poor GPS)
RECENT = timedelta(minutes=30)  # older transitions (phone was offline) update the state but don't notify


@dataclass
class Point:
    lat: float
    lng: float
    accuracy: float | None
    at: datetime


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres (haversine)."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def next_state(inside: bool | None, dist: float, radius: int) -> bool:
    """Enter at the edge, leave only when clearly outside (stops GPS jitter from causing repeated alerts)."""
    if inside:
        return dist < radius + max(30.0, radius * 0.2)
    return dist <= radius


def evaluate(child: Child, points: list[Point]) -> list[dict]:
    """Updates every place's inside/outside state from new points (oldest first).
    Returns the alerts to send: at most one per place, and none for the very first reading."""
    usable = sorted((p for p in points if p.accuracy is None or p.accuracy <= MAX_ACCURACY_M), key=lambda p: p.at)
    if not usable or not child.places:
        return []
    alerts = []
    for place in child.places:
        start = state = place.inside
        changed_at = None
        for p in usable:
            new = next_state(state, distance_m(p.lat, p.lng, place.lat, place.lng), place.radius_m)
            if new != state:
                state, changed_at = new, p.at
        if state == start:
            continue
        place.inside = state
        place.state_changed_at = changed_at or usable[-1].at
        if start is None:  # first time we know where the child is: no alert
            continue
        if utcnow() - place.state_changed_at > RECENT:
            continue
        verb = "arrived at" if state else "left"
        alerts.append({
            "title": f"{child.name} {verb} {place.name}",
            "body": "Based on the phone's latest location.",
            "data": {"type": "place_arrived" if state else "place_left", "child_id": child.id, "place_id": place.id},
        })
    return alerts
