from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import settings
from .models import entities  # noqa: F401  (registers tables)
from .models.db import Base, SessionLocal, engine
from .routes import auth, children, device
from .services.retention import purge_old_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        purge_old_data(db)
    yield


app = FastAPI(title="ParentalGuardian API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(children.router)
app.include_router(device.router)


@app.get("/health")
def health():
    return {"status": "ok"}
