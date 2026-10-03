import pytest
from httpx import ASGITransport, AsyncClient

from meraki import Meraki
from meraki.core.response import Response
from meraki.plugins import Plugin


def test_register_plugin_calls_register_with_app():
    app = Meraki()
    seen = []

    class MyPlugin(Plugin):
        name = "my-plugin"

        def register(self, app):
            seen.append(app)

    plugin = MyPlugin()
    result = app.register_plugin(plugin)

    assert result is plugin
    assert seen == [app]
    assert app.plugin_manager.get("my-plugin") is plugin
    assert app.plugin_manager.plugins == [plugin]


def test_register_plugin_rejects_non_plugin():
    app = Meraki()
    with pytest.raises(TypeError):
        app.register_plugin(object())


def test_register_plugin_rejects_duplicate_name():
    app = Meraki()

    class Dup(Plugin):
        name = "dup"

    app.register_plugin(Dup())
    with pytest.raises(ValueError, match="already registered"):
        app.register_plugin(Dup())


def test_plugin_can_register_route_and_middleware():
    app = Meraki()

    async def plugin_mw(request, call_next):
        resp = await call_next(request)
        resp.headers.append((b"x-plugin", b"true"))
        return resp

    class WebPlugin(Plugin):
        name = "web"

        def register(self, app):
            app.add_middleware(plugin_mw)

            @app.get("/from-plugin")
            async def handler(request):
                return Response(body=b"plugin says hi")

    app.register_plugin(WebPlugin())

    # route + middleware should work end-to-end via ASGI
    async def run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            res = await client.get("/from-plugin")
            assert res.status_code == 200
            assert res.text == "plugin says hi"
            assert res.headers["x-plugin"] == "true"

    import asyncio
    asyncio.run(run())


def test_plugin_services():
    app = Meraki()

    class SvcPlugin(Plugin):
        name = "svc"

        def register(self, app):
            app.add_service("greeting", "hello")

    app.register_plugin(SvcPlugin())
    assert app.get_service("greeting") == "hello"
    assert app.get_service("missing") is None
    assert app.get_service("missing", "fallback") == "fallback"


@pytest.mark.asyncio
async def test_plugin_lifespan_startup_shutdown_order():
    app = Meraki()
    events = []

    class A(Plugin):
        name = "a"

        async def on_startup(self):
            events.append("a_start")

        async def on_shutdown(self):
            events.append("a_stop")

    class B(Plugin):
        name = "b"

        def on_startup(self):  # sync hooks must also work
            events.append("b_start")

        def on_shutdown(self):
            events.append("b_stop")

    app.register_plugin(A())
    app.register_plugin(B())

    await app.plugin_manager.startup()
    assert events == ["a_start", "b_start"]

    await app.plugin_manager.shutdown()
    assert events == ["a_start", "b_start", "b_stop", "a_stop"]


@pytest.mark.asyncio
async def test_lifespan_asgi_calls_plugin_hooks():
    app = Meraki()
    calls = []

    class L(Plugin):
        name = "lifecycle"

        async def on_startup(self):
            calls.append("startup")

        async def on_shutdown(self):
            calls.append("shutdown")

    app.register_plugin(L())

    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    sent = []

    async def receive():
        return messages.pop(0)

    async def send(msg):
        sent.append(msg)

    await app({"type": "lifespan"}, receive, send)

    assert calls == ["startup", "shutdown"]
    assert sent[0]["type"] == "lifespan.startup.complete"
    assert sent[1]["type"] == "lifespan.shutdown.complete"
