"""ASGI request abstraction.

``Request`` wraps the ASGI ``scope``/``receive`` pair so handlers work with
a stable framework object instead of server-specific details.
"""

import json as _json
from http.cookies import SimpleCookie
from urllib.parse import parse_qsl, urlencode


class Request:
    def __init__(self, scope, receive):
        if scope.get("type") not in ("http", "websocket"):
            raise ValueError(f"Unsupported scope type: {scope.get('type')!r}")
        self.scope = scope
        self._receive = receive
        self.method = scope.get("method", "GET").upper()
        self.path = scope.get("path", "/") or "/"
        self.query_string = scope.get("query_string", b"").decode("latin-1")
        self.query_params = self._parse_query(self.query_string)
        self.headers = self._parse_headers(scope.get("headers", []))
        self.cookies = self._parse_cookies(self.headers.get("cookie", ""))
        self.path_params = {}
        self.app = None  # set by the application before dispatch
        self.state = {}  # per-request storage for middleware/handlers
        self._body = None

    @staticmethod
    def _parse_query(query_string):
        params = {}
        for key, value in parse_qsl(query_string, keep_blank_values=True):
            if key in params:
                existing = params[key]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    params[key] = [existing, value]
            else:
                params[key] = value
        return params

    @staticmethod
    def _parse_headers(raw_headers):
        headers = {}
        for name, value in raw_headers:
            key = name.decode("latin-1").lower()
            val = value.decode("latin-1")
            if key in headers:
                headers[key] = f"{headers[key]}, {val}"
            else:
                headers[key] = val
        return headers

    @staticmethod
    def _parse_cookies(cookie_header):
        if not cookie_header:
            return {}
        jar = SimpleCookie()
        try:
            jar.load(cookie_header)
        except Exception:
            return {}
        return {key: morsel.value for key, morsel in jar.items()}

    @property
    def url(self):
        scheme = self.scope.get("scheme", "http")
        server = self.scope.get("server")
        host = self.headers.get("host") or (f"{server[0]}:{server[1]}" if server else "localhost")
        query = f"?{self.query_string}" if self.query_string else ""
        return f"{scheme}://{host}{self.path}{query}"

    async def body(self) -> bytes:
        if self._body is None:
            chunks = []
            while True:
                message = await self._receive()
                if message.get("type") == "http.request":
                    chunks.append(message.get("body", b""))
                    if not message.get("more_body"):
                        break
                elif message.get("type") == "http.disconnect":  # pragma: no cover
                    break
            self._body = b"".join(chunks)
        return self._body

    async def text(self) -> str:
        return (await self.body()).decode("utf-8", errors="replace")

    async def json(self):
        raw = await self.body()
        if not raw:
            return None
        return _json.loads(raw.decode("utf-8"))

    async def form(self):
        """Parse ``application/x-www-form-urlencoded`` bodies."""
        ctype = self.headers.get("content-type", "").split(";")[0].strip()
        if ctype != "application/x-www-form-urlencoded":
            return {}
        return self._parse_query((await self.body()).decode("utf-8", errors="replace"))

    def __repr__(self):  # pragma: no cover - trivial
        return f"Request({self.method} {self.path})"
