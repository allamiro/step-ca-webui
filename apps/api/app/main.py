from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
import time

from app.api.auth import router as auth_router
from app.api.ca import router as ca_router
from app.api.certificates import router as certificates_router
from app.api.jobs import router as jobs_router
from app.api.misc import router as misc_router
from app.api.scim import router as scim_router
from app.core.config import settings
from app.core.db import Base, engine

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    # Postgres container may be up before it's ready for TCP connections.
    for _ in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            time.sleep(2)
    raise RuntimeError("Database is not ready after retries")


@app.get("/")
def root():
    return {"service": "pki-api", "status": "ok"}


app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(ca_router, prefix=settings.api_prefix)
app.include_router(certificates_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(misc_router, prefix=settings.api_prefix)
app.include_router(scim_router)
