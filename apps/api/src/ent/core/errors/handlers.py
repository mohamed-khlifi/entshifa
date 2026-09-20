"""Map domain errors to RFC 7807 problem+json responses."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ent.core.context import get_request_id
from ent.core.errors.exceptions import DomainError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(
        _request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        body: dict[str, Any] = {
            "type": f"https://errors.entapp.io/{exc.code.replace('.', '/')}",
            "title": exc.code,
            "status": exc.http_status,
            "code": exc.code,
            "detail": None,
            "context": exc.context,
            "requestId": get_request_id(),
        }
        return JSONResponse(status_code=exc.http_status, content=body)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        body = {
            "type": "https://errors.entapp.io/internal_error",
            "title": "internal_error",
            "status": 500,
            "code": "internal_error",
            "detail": None,
            "context": {},
            "requestId": get_request_id(),
        }
        return JSONResponse(status_code=500, content=body)
