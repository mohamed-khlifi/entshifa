"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ent.core.audit.hooks import install_audit_listeners
from ent.core.audit.middleware import RequestContextMiddleware
from ent.core.db.session import dispose_engine
from ent.core.errors.handlers import register_exception_handlers
from ent.features.auth.router import router as auth_router
from ent.features.health.router import router as health_router
from ent.integrations.redis import close_redis
from ent.settings import Settings, load_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    install_audit_listeners()
    yield
    await dispose_engine()
    await close_redis()


def create_app(settings: Settings | None = None) -> FastAPI:
    install_audit_listeners()
    resolved = settings or load_settings()
    app = FastAPI(
        title="EntShifa API",
        version="0.0.0",
        lifespan=lifespan,
    )
    app.state.settings = resolved

    # Starlette runs last-added middleware outermost; CORS should wrap responses.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    return app
