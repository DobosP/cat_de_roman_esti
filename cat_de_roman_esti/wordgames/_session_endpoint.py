"""Shared transaction boundary for server-authoritative game session endpoints."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from ..web.http import http_error
from .service import SessionStore

S = TypeVar("S")
EndpointMethod = Callable[..., Any]


def atomic_session(
    store_getter: Callable[[], SessionStore[S]],
    missing_detail: str,
) -> Callable[[EndpointMethod], EndpointMethod]:
    """Run an endpoint method inside one pinned, exclusive session transaction.

    ``store_getter`` is evaluated for every request so tests and alternate runtime
    wiring can replace a game's module-level store without leaving decorated views
    attached to the previous instance.
    """

    def decorate(method: EndpointMethod) -> EndpointMethod:
        @wraps(method)
        def wrapped(self: object, request: object, game_id: str) -> Any:
            with store_getter().transaction(game_id) as session:
                if session is None:
                    raise http_error(404, missing_detail)
                return method(self, request, game_id, session)

        return wrapped

    return decorate
