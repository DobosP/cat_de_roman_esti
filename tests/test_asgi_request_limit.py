"""The body ceiling must apply before Django's ASGI handler buffers chunks."""

from __future__ import annotations

import asyncio
import json

from cat_de_roman_esti.web.asgi_limits import RequestBodyLimitASGI


def _scope(headers=()):
    return {
        "type": "http",
        "method": "POST",
        "path": "/api/test",
        "headers": list(headers),
    }


def test_chunked_body_is_stopped_at_the_receive_boundary() -> None:
    messages = iter(
        [
            {"type": "http.request", "body": b"a" * 40, "more_body": True},
            {"type": "http.request", "body": b"b" * 30, "more_body": True},
            {"type": "http.request", "body": b"c" * 100, "more_body": False},
        ]
    )
    receive_calls = 0
    forwarded = bytearray()
    sent = []

    async def receive():
        nonlocal receive_calls
        receive_calls += 1
        return next(messages)

    async def send(message):
        sent.append(message)

    async def downstream(scope, limited_receive, downstream_send):
        while True:
            message = await limited_receive()
            forwarded.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break

    asyncio.run(RequestBodyLimitASGI(downstream, 64)(_scope(), receive, send))

    assert receive_calls == 2
    assert forwarded == b"a" * 40  # The crossing chunk never reaches Django.
    assert sent[0]["status"] == 413
    assert json.loads(sent[1]["body"]) == {"detail": "Request body too large"}


def test_declared_oversize_is_rejected_without_reading() -> None:
    receive_calls = 0
    app_called = False
    sent = []

    async def receive():
        nonlocal receive_calls
        receive_calls += 1
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    async def downstream(scope, downstream_receive, downstream_send):
        nonlocal app_called
        app_called = True

    asyncio.run(
        RequestBodyLimitASGI(downstream, 64)(_scope([(b"content-length", b"65")]), receive, send)
    )

    assert not app_called
    assert receive_calls == 0
    assert sent[0]["status"] == 413


def test_body_at_limit_passes_through_unchanged() -> None:
    messages = iter(
        [
            {"type": "http.request", "body": b"a" * 32, "more_body": True},
            {"type": "http.request", "body": b"b" * 32, "more_body": False},
        ]
    )
    forwarded = bytearray()
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    async def downstream(scope, limited_receive, downstream_send):
        while True:
            message = await limited_receive()
            forwarded.extend(message.get("body", b""))
            if not message.get("more_body", False):
                break
        await downstream_send({"type": "http.response.start", "status": 204, "headers": []})
        await downstream_send({"type": "http.response.body", "body": b""})

    asyncio.run(RequestBodyLimitASGI(downstream, 64)(_scope(), receive, send))

    assert forwarded == (b"a" * 32) + (b"b" * 32)
    assert sent[0]["status"] == 204
