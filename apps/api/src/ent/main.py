"""FastAPI application factory."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from ent.core.context import set_request_id
from ent.core.db.session import dispose_engine
from ent.core.errors.handlers import register_exception_handlers
from ent.features.auth.router import router as auth_router
from ent.features.health.router import router as health_router
from ent.integrations.redis import close_redis
from ent.settings import Settings, load_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()
    await close_redis()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or load_settings()
    app = FastAPI(
        title="EntShifa API",
        version="0.0.0",
        lifespan=lifespan,
    )
    app.state.settings = resolved

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def attach_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get("X-Request-Id")
        set_request_id(incoming or str(uuid.uuid4()))
        return await call_next(request)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(auth_router)
    return app
