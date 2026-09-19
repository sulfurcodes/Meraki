import asyncio
import json

from meraki import Meraki
from meraki.middleware import CORSMiddleware, LoggerMiddleware
from tests.helpers import call_app, make_scope


def test_middleware_order_and_post_processing():
    order = []
    app = Meraki()

    async def m1(request, call_next):
        order.append("m1-before")
        resp = await call_next(request)
        order.append("m1-after")
        return resp

    async def m2(request, call_next):
        order.append("m2-before")
        resp = await call_next(request)
        order.append("m2-after")
        return resp

    app.add_middleware(m1)
    app.add_middleware(m2)

    @app.get("/x")
    def x(request):
        order.append("handler")
        return {"ok": True}

    status, _, _ = call_app(app, "GET", "/x")
    assert status == 200
    assert order == ["m1-before", "m2-before", "handler", "m2-after", "m1-after"]


def test_short_circuit():
    from meraki import Response

    app = Meraki()

    async def guard(request, call_next):
        if request.path == "/blocked":
            return Response("nope", status_code=403)
        return await call_next(request)

    app.add_middleware(guard)

    @app.get("/blocked")
    def h(request):  # pragma: no cover
        return {"never": True}

    status, _, body = call_app(app, "GET", "/blocked")
    assert status == 403
    assert body == b"nope"


def test_sync_function_middleware():
    app = Meraki()
    seen = []

    def mw(request, call_next):
        seen.append(request.path)
        return call_next(request)

    app.add_middleware(mw)

    @app.get("/s")
    def h(request):
        return "sync-ok"

    status, _, body = call_app(app, "GET", "/s")
    assert status == 200 and body == b"sync-ok" and seen == ["/s"]


def test_cors_preflight_and_headers():
    app = Meraki(middleware=[CORSMiddleware()])

    @app.get("/data")
    def h(request):
        return {"d": 1}

    status, headers, _ = call_app(app, "OPTIONS", "/data")
    assert status == 204
    assert headers.get("access-control-allow-origin") == "*"

    status, headers, _ = call_app(app, "GET", "/data")
    assert status == 200
    assert headers.get("access-control-allow-origin") == "*"


def test_logger_middleware_runs():
    records = []
    app = Meraki(middleware=[LoggerMiddleware(records.append)])

    @app.get("/l")
    def h(request):
        return "ok"

    status, _, _ = call_app(app, "GET", "/l")
    assert status == 200
    assert len(records) == 1 and "GET /l -> 200" in records[0]


def test_request_parsing():
    from meraki import Request

    async def receive():
        return {"type": "http.request", "body": b'{"k": "v"}', "more_body": False}

    scope = make_scope("POST", "/s", "a=1&a=2&b=3",
                       {"content-type": "application/json", "x-test": "yes",
                        "cookie": "session=abc"})
    req = Request(scope, receive)
    assert req.method == "POST"
    assert req.query_params == {"a": ["1", "2"], "b": "3"}
    assert req.headers["x-test"] == "yes"
    assert req.cookies == {"session": "abc"}
    assert asyncio.run(req.json()) == {"k": "v"}
