"""RiskLens FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .db.session import Base, engine
from . import models  # noqa: F401  (register models on Base)
from .api.routes import auth, builder, calculations, instruments, monitoring, portfolios

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risklens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured; environment=%s", settings.environment)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "RiskLens — fixed-income intelligence, portfolio optimisation and risk "
        "analytics (Indian market focus). ALL bundled data is SIMULATED. Not "
        "investment advice; yields/liquidity are indicative, not guaranteed."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.app_name, "data_status": "SIMULATED"}


@app.get("/", tags=["system"])
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "disclaimer": "All bundled data is SIMULATED. Not investment advice.",
    }


app.include_router(auth.router)
app.include_router(instruments.router)
app.include_router(calculations.router)
app.include_router(portfolios.router)
app.include_router(builder.router)
app.include_router(monitoring.router)
