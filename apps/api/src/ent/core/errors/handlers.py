"""Map domain and framework errors to RFC 7807 problem+json."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.alias_generators import to_camel
from starlette.exceptions import HTTPException as StarletteHTTPException

from ent.core.context import get_request_id
from ent.core.errors.codes import ErrorCode
from ent.core.errors.exceptions import DomainError

logger = logging.getLogger("ent.errors")


def _problem(
    *,
    code: str,
    status: int,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": f"https://errors.entapp.io/{code.replace('.', '/')}",
        "title": code,
        "status": status,
        "code": code,
        "detail": None,
        "context": context or {},
        "requestId": get_request_id(),
    }


def _loc_to_camel(loc: tuple[Any, ...]) -> str:
    parts: list[str] = []
    for item in loc:
        if item in {"body", "query", "path", "header", "cookie"}:
            continue
        if isinstance(item, int):
            parts.append(str(item))
        else:
            parts.append(to_camel(str(item)))
    return ".".join(parts)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(
        _request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=_problem(code=exc.code, status=exc.http_status, context=exc.context),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        fields: dict[str, str] = {}
        for error in exc.errors():
            path = _loc_to_camel(tuple(error.get("loc", ())))
            fields[path or "body"] = str(error.get("type", "value_error"))
        return JSONResponse(
            status_code=422,
            content=_problem(
                code=ErrorCode.VALIDATION_FAILED,
                status=422,
                context={"fields": fields},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        code = ErrorCode.NOT_FOUND if exc.status_code == 404 else ErrorCode.DOMAIN_ERROR
        if exc.status_code == 401:
            code = ErrorCode.AUTH_UNAUTHENTICATED
        elif exc.status_code == 403:
            code = ErrorCode.FORBIDDEN
        return JSONResponse(
            status_code=exc.status_code,
            content=_problem(code=code, status=exc.status_code),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        request_id = get_request_id()
        logger.exception(
            "Unhandled exception request_id=%s",
            request_id,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content=_problem(code=ErrorCode.INTERNAL_ERROR, status=500),
        )
