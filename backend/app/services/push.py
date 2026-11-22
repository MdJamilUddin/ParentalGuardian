import base64
import json
import logging

from sqlalchemy.orm import Session

from ..config.settings import settings
from ..models.db import SessionLocal
from ..models.entities import PushToken, utcnow

log = logging.getLogger("app.push")


class NullSender:
    """Used when Firebase is not configured: notifications are logged, not sent."""
    configured = False

    def send(self, tokens, title, body, data):
        log.info("push disabled (no Firebase credentials): %s", title)
        return []


class FCMSender:
    configured = True

    def __init__(self, credentials: str):
        import firebase_admin
        from firebase_admin import credentials as fb_credentials

        raw = credentials.strip()
        if not raw.startswith("{"):  # allow base64 so the JSON fits in one environment variable line
            raw = base64.b64decode(raw).decode()
        self.app = firebase_admin.initialize_app(fb_credentials.Certificate(json.loads(raw)))

    def send(self, tokens, title, body, data):
        """Returns the tokens that are no longer valid (app uninstalled, token rotated)."""
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in data.items()},
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(channel_id="alerts"),
            ),
        )
        response = messaging.send_each_for_multicast(message, app=self.app)
        invalid = []
        for token, r in zip(tokens, response.responses):
            if not r.success and isinstance(r.exception, (messaging.UnregisteredError, messaging.SenderIdMismatchError)):
                invalid.append(token)
        return invalid


_sender = None


def get_sender():
    global _sender
    if _sender is None:
        if settings.FIREBASE_CREDENTIALS_JSON:
            try:
                _sender = FCMSender(settings.FIREBASE_CREDENTIALS_JSON)
            except Exception:
                log.exception("Firebase credentials are invalid; push notifications are disabled")
                _sender = NullSender()
        else:
            _sender = NullSender()
    return _sender


def set_sender(sender) -> None:  # tests
    global _sender
    _sender = sender


def notify_parent(db: Session, parent_id: int, title: str, body: str, data: dict | None = None) -> int:
    """Sends a notification to all of a parent's phones. Returns how many phones were targeted successfully."""
    tokens = [t.token for t in db.query(PushToken).filter(PushToken.parent_id == parent_id).all()]
    if not tokens:
        return 0
    sender = get_sender()
    try:
        invalid = sender.send(tokens, title, body, data or {})
    except Exception:
        log.exception("push send failed")
        return 0
    if invalid:
        db.query(PushToken).filter(PushToken.token.in_(invalid)).delete(synchronize_session=False)
        db.commit()
    return len(tokens) - len(invalid)


def push_to_parent(parent_id: int, title: str, body: str, data: dict | None = None) -> None:
    """Background-task entry point (opens its own database session)."""
    with SessionLocal() as db:
        notify_parent(db, parent_id, title, body, data)
