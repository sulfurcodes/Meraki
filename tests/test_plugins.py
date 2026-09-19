import json

from meraki import Meraki, Plugin
from meraki.plugins import PluginManager
from meraki.exceptions import PluginError
from tests.helpers import call_app, lifespan


def test_plugin_registers_routes_and_middleware():
    events = []

    class DemoPlugin(Plugin):
        name = "demo"

        def register(self, app):
            async def mw(request, call_next):
                events.append("mw")
                return await call_next(request)

            app.add_middleware(mw)

            @app.get("/from-plugin")
            def h(request):
                return {"plugin": True}

    app = Meraki(plugins=[DemoPlugin()])
    assert "demo" in app.plugins
    status, _, body = call_app(app, "GET", "/from-plugin")
    assert status == 200
    assert json.loads(body) == {"plugin": True}
    assert events == ["mw"]


def test_plugin_lifecycle_and_services():
    calls = []

    class Svc:
        def __init__(self):
            self.closed = False

    class LifecyclePlugin(Plugin):
        name = "life"

        def register(self, app):
            app.add_service("svc", Svc())

        async def on_startup(self, app):
            calls.append(("startup", app.get_service("svc") is not None))

        async def on_shutdown(self, app):
            calls.append(("shutdown", app.get_service("svc") is not None))

    app = Meraki(plugins=[LifecyclePlugin()])
    messages = lifespan(app)
    types = [m["type"] for m in messages]
    assert types == ["lifespan.startup.complete", "lifespan.shutdown.complete"]
    assert calls == [("startup", True), ("shutdown", True)]


def test_duplicate_plugin_name_rejected():
    class P(Plugin):
        name = "dup"

    manager = PluginManager()
    manager.register(P())
    try:
        manager.register(P())
    except PluginError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected PluginError")


def test_invalid_plugin_rejected():
    manager = PluginManager()
    try:
        manager.register(object())
    except PluginError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected PluginError")


def test_app_lifecycle_hooks():
    order = []
    app = Meraki()

    @app.on_startup
    def boot():
        order.append("up")

    @app.on_shutdown
    async def down():
        order.append("down")

    messages = lifespan(app)
    assert [m["type"] for m in messages] == [
        "lifespan.startup.complete", "lifespan.shutdown.complete",
    ]
    assert order == ["up", "down"]
