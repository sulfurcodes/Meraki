"""ASGI response abstractions."""

import json as _json
from http import HTTPStatus


def _status_line(status_code):
    try:
        phrase = HTTPStatus(status_code).phrase
    except ValueError:
        phrase = "Unknown"
    return f"{status_code} {phrase}"


class Response:
    def __init__(self, content=b"", status_code=200, headers=None, media_type="text/plain"):
        if isinstance(content, str):
            content = content.encode("utf-8")
        elif isinstance(content, (dict, list)):
            content = _json.dumps(content).encode("utf-8")
            media_type = "application/json"
        elif content is None:
            content = b""
        elif not isinstance(content, (bytes, bytearray)):
            content = str(content).encode("utf-8")
        self.body = bytes(content)
        self.status_code = int(status_code)
        self.media_type = media_type
        self.headers = list(headers) if headers else []
        if media_type and not any(k.lower() == "content-type" for k, _ in self.headers):
            self.headers.append(("content-type", f"{media_type}; charset=utf-8"))

    def set_header(self, name, value):
        lname = name.lower()
        self.headers = [(k, v) for k, v in self.headers if k.lower() != lname]
        self.headers.append((name, value))

    async def __call__(self, scope, receive, send):
        raw_headers = [
            (k.lower().encode("latin-1") if isinstance(k, str) else k,
             v.encode("latin-1") if isinstance(v, str) else v)
            for k, v in self.headers
        ]
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": raw_headers,
        })
        await send({"type": "http.response.body", "body": self.body})

    @property
    def status(self):  # human-readable alias, e.g. "200 OK"
        return _status_line(self.status_code)

    def __repr__(self):  # pragma: no cover - trivial
        return f"Response({self.status})"


class PlainTextResponse(Response):
    def __init__(self, content="", status_code=200, headers=None):
        super().__init__(content, status_code, headers, media_type="text/plain")


class HTMLResponse(Response):
    def __init__(self, content="", status_code=200, headers=None):
        super().__init__(content, status_code, headers, media_type="text/html")


class JSONResponse(Response):
    def __init__(self, content=None, status_code=200, headers=None):
        super().__init__(_json.dumps(content).encode("utf-8"), status_code, headers,
                         media_type="application/json")
