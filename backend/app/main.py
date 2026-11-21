import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config.settings import settings
from .logging_config import setup_logging
from .migrate import run_migrations
from .models.db import SessionLocal, get_db
from .routes import auth, children, device
from .services.retention import purge_old_data

setup_logging()
access_log = logging.getLogger("app.access")

if settings.SENTRY_DSN:  # optional error tracking; no personal data is attached to events
    import sentry_sdk

    sentry_sdk.init(dsn=settings.SENTRY_DSN, environment=settings.ENVIRONMENT,
                    send_default_pii=False, traces_sample_rate=0.0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.AUTO_MIGRATE:
        run_migrations()
    with SessionLocal() as db:
        purge_old_data(db)
    yield


app = FastAPI(title="ParentalGuardian API", version="0.2.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def access_logging(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        access_log.exception("unhandled error", extra={"request_id": rid, "method": request.method,
                                                       "path": request.url.path})
        raise
    response.headers["X-Request-ID"] = rid
    if not request.url.path.startswith("/health"):  # keep health checks out of the logs
        status = response.status_code
        access_log.log(
            logging.WARNING if status >= 500 else logging.INFO,
            "%s %s %s", request.method, request.url.path, status,
            extra={"request_id": rid, "method": request.method, "path": request.url.path,
                   "status": status, "duration_ms": round((time.perf_counter() - start) * 1000)},
        )
    return response


app.include_router(auth.router)
app.include_router(children.router)
app.include_router(device.router)


@app.get("/health")
def health():
    """Liveness: the process is up."""
    return {"status": "ok"}


@app.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: the process can reach the database."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ok", "database": "ok"}
