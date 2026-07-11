"""ASGI transport guards that run before Django buffers a request body."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

Scope = dict[str, Any]
Message = dict[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
AsgiApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_TOO_LARGE_BODY = b'{"detail":"Request body too large"}'


class _RequestBodyTooLarge(Exception):
    """Internal control flow raised before an oversized chunk reaches Django."""


class RequestBodyLimitASGI:
    """Reject bodies above ``max_body_bytes`` at the ASGI receive boundary.

    Django's ASGI handler spools the entire request before it constructs an
    ``HttpRequest``. A view/middleware ``Content-Length`` check is therefore too
    late for chunked requests. This wrapper counts chunks as the server exposes
    them and stops forwarding as soon as the limit is crossed.
    """

    def __init__(self, app: AsgiApp, max_body_bytes: int | None) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or self.max_body_bytes is None:
            await self.app(scope, receive, send)
            return

        declared_length = self._content_length(scope)
        if declared_length is not None and declared_length > self.max_body_bytes:
            await self._send_too_large(send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    raise _RequestBodyTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestBodyTooLarge:
            if response_started:  # Defensive; Django reads fully before responding.
                raise
            await self._send_too_large(send)

    @staticmethod
    def _content_length(scope: Scope) -> int | None:
        for name, value in scope.get("headers", ()):
            if name.lower() != b"content-length":
                continue
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                return None
            return max(parsed, 0)
        return None

    @staticmethod
    async def _send_too_large(send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(_TOO_LARGE_BODY)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": _TOO_LARGE_BODY})
