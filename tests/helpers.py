"""Shared ASGI test helpers (stdlib only — no test server needed)."""

import asyncio
import json


def make_scope(method="GET", path="/", query_string="", headers=None, scheme="http"):
    raw_headers = [
        (k.lower().encode("latin-1"), v.encode("latin-1"))
        for k, v in (headers or {}).items()
    ]
    return {
        "type": "http",
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": scheme,
        "path": path,
        "query_string": query_string.encode("latin-1"),
        "headers": raw_headers,
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
    }


def call_app(app, method="GET", path="/", query_string="", headers=None, body=b""):
    """Drive an ASGI app synchronously; return (status, headers, body)."""
    if isinstance(body, (dict, list)):
        body = json.dumps(body).encode()
        headers = {"content-type": "application/json", **(headers or {})}
    if isinstance(body, str):
        body = body.encode()

    scope = make_scope(method, path, query_string, headers)
    messages = [{"type": "http.request", "body": body, "more_body": False}]
    sent = []

    async def receive():
        if messages:
            return messages.pop(0)
        return {"type": "http.disconnect"}  # pragma: no cover

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    chunks = [m.get("body", b"") for m in sent if m["type"] == "http.response.body"]
    headers_out = {
        k.decode("latin-1"): v.decode("latin-1") for k, v in start.get("headers", [])
    }
    return start["status"], headers_out, b"".join(chunks)


def lifespan(app):
    """Run startup+shutdown over the lifespan protocol; return sent messages."""
    sent = []
    received_startup = False

    async def receive():
        nonlocal received_startup
        if not received_startup:
            received_startup = True
            return {"type": "lifespan.startup"}
        return {"type": "lifespan.shutdown"}

    async def send(message):
        sent.append(message)

    async def run():
        await app({"type": "lifespan"}, receive, send)

    asyncio.run(run())
    return sent
