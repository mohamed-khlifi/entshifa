"""Request context middleware (request id, IP, user-agent)."""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ent.core.context import set_ip_address, set_request_id, set_user_agent
from ent.core.utils.ids import new_ulid


class RequestContextMiddleware:
    """Pure ASGI middleware so FastAPI exception handlers still run."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        incoming = headers.get("x-request-id")
        request_id = incoming if incoming and len(incoming) == 26 else new_ulid()
        set_request_id(request_id)

        forwarded = headers.get("x-forwarded-for")
        if forwarded:
            set_ip_address(forwarded.split(",")[0].strip())
        else:
            client = scope.get("client")
            set_ip_address(client[0] if client else None)

        set_user_agent(headers.get("user-agent"))

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers: list[tuple[bytes, bytes]] = list(
                    message.get("headers", [])
                )
                raw_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = {**message, "headers": raw_headers}
            await send(message)

        await self.app(scope, receive, send_with_request_id)
