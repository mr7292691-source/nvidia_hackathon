from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, approvals, decisions, evidence, events, replay
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.nvidia_runtime.relay.guardrails import register_all_guardrails
from app.nvidia_runtime.relay.relay_runtime import init_relay


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_relay()
    register_all_guardrails()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="LifeShield AI", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.app_cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(events.router)
    app.include_router(evidence.router)
    app.include_router(agents.router)
    app.include_router(decisions.router)
    app.include_router(approvals.router)
    app.include_router(replay.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "env": settings.lifeshield_env}

    return app


app = create_app()
