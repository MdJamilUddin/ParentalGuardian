import hmac

from fastapi import APIRouter, Header, HTTPException

from ..config.settings import settings
from ..services.alerts import run_alert_check

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/check-alerts")
def check_alerts(x_cron_secret: str | None = Header(default=None)):
    """For an external scheduler (also wakes a sleeping free-tier host). Disabled unless CRON_SECRET is set."""
    if not settings.CRON_SECRET:
        raise HTTPException(404)
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret, settings.CRON_SECRET):
        raise HTTPException(401)
    return {"offline_alerts": run_alert_check()}
