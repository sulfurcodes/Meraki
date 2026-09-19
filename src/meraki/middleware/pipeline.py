"""Middleware pipeline.

A middleware wraps request handling with the signature::

    async def __call__(self, request, call_next) -> Response

``call_next`` invokes the rest of the pipeline (remaining middleware +
route handler). Returning a response without calling ``call_next``
short-circuits the pipeline. Plain functions (sync or async) with the
same signature work too — no subclassing required.
"""

import inspect
import logging
import time

logger = logging.getLogger("meraki")


async def _maybe_await(value):
    if inspect.isawaitable(value):
        return await value
    return value


class BaseMiddleware:
    """Convenience base class; subclass and override ``__call__``."""

    async def __call__(self, request, call_next):
        return await call_next(request)


class LoggerMiddleware(BaseMiddleware):
    """Logs ``METHOD path -> status (ms)`` for every request."""

    def __init__(self, logger_factory=None):
        self._log = logger_factory or logger.info

    async def __call__(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        try:
            self._log(f"{request.method} {request.path} -> {response.status_code} ({elapsed_ms:.1f}ms)")
        except Exception:  # logging must never break responses
            pass
        return response


class CORSMiddleware(BaseMiddleware):
    """Adds CORS headers to every response and answers preflights.

    A bare ``OPTIONS`` request is short-circuited with ``204`` so routes
    don't need to handle preflights themselves.
    """

    def __init__(self, allow_origins=None, allow_methods=None, allow_headers=None,
                 max_age="86400", allow_credentials=False):
        self.allow_origins = allow_origins if allow_origins is not None else ["*"]
        self.allow_methods = allow_methods if allow_methods is not None else [
            "GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD",
        ]
        self.allow_headers = allow_headers if allow_headers is not None else [
            "Content-Type", "Authorization",
        ]
        self.max_age = str(max_age)
        self.allow_credentials = allow_credentials

    def _origin_value(self, request):
        if "*" in self.allow_origins:
            return "*" if not self.allow_credentials else request.headers.get("origin", "*")
        origin = request.headers.get("origin", "")
        if origin in self.allow_origins:
            return origin
        return self.allow_origins[0] if self.allow_origins else "*"

    @staticmethod
    def _join(values):
        if isinstance(values, str):
            return values
        return ", ".join(values)

    async def __call__(self, request, call_next):
        from ..core.response import Response

        origin = self._origin_value(request)
        if request.method == "OPTIONS":
            response = Response(b"", status_code=204)
            response.set_header("access-control-allow-origin", origin)
            response.set_header("access-control-allow-methods", self._join(self.allow_methods))
            response.set_header("access-control-allow-headers", self._join(self.allow_headers))
            response.set_header("access-control-max-age", self.max_age)
            return response
        response = await call_next(request)
        response.set_header("access-control-allow-origin", origin)
        response.set_header("access-control-allow-methods", self._join(self.allow_methods))
        response.set_header("access-control-allow-headers", self._join(self.allow_headers))
        if self.allow_credentials:
            response.set_header("access-control-allow-credentials", "true")
        return response


class TrustedHostMiddleware(BaseMiddleware):
    """Rejects requests whose Host is not in the allow-list (``400``)."""

    def __init__(self, allowed_hosts=None):
        self.allowed_hosts = allowed_hosts or ["*"]

    async def __call__(self, request, call_next):
        from ..core.response import JSONResponse

        if "*" in self.allowed_hosts:
            return await call_next(request)
        host = request.headers.get("host", "").split(":")[0]
        if host not in self.allowed_hosts:
            return JSONResponse({"error": f"Host {host!r} is not allowed"}, status_code=400)
        return await call_next(request)
