"""Central application object.

``Meraki`` coordinates routing, middleware, configuration, plugins, and
error handling behind a single ASGI callable that Uvicorn can serve::

    app = Meraki()
    app.router.get("/hello")(hello)
    app.run()
"""

import inspect

from .config.settings import Settings
from .core.lifecycle import Lifecycle
from .core.request import Request
from .core.response import JSONResponse, Response
from .exceptions.base import HTTPException, MethodNotAllowed, NotFound
from .plugins.manager import PluginManager
from .routing.router import Router


async def _await_value(value):
    if inspect.isawaitable(value):
        return await value
    return value


class Meraki:
    def __init__(self, title=None, debug=None, middleware=None, plugins=None, **config):
        self.settings = Settings(**config)
        if title is not None:
            self.settings.set("TITLE", title)
        if debug is not None:
            self.settings.set("DEBUG", bool(debug))
        self.router = Router()
        self.lifecycle = Lifecycle()
        self.plugins = PluginManager()
        self.state = {}  # shared services / plugin state
        self._middleware = []
        self._exception_handlers = {}
        for mw in middleware or []:
            self.add_middleware(mw)
        for plugin in plugins or []:
            self.include_plugin(plugin)

    # -- wiring ---------------------------------------------------------
    def add_middleware(self, middleware):
        """Register ``middleware`` (instance, class, or ``(req, call_next)`` function)."""
        if inspect.isclass(middleware):
            middleware = middleware()
        self._middleware.append(middleware)
        return middleware

    @property
    def middleware(self):
        return list(self._middleware)

    def include_plugin(self, plugin_like):
        plugin = self.plugins.register(plugin_like)
        # registration is sync-friendly: run now so routes exist immediately
        result = plugin.register(self)
        if inspect.isawaitable(result):  # pragma: no cover - unusual path
            raise RuntimeError(
                f"Plugin {plugin.name!r}.register() must be synchronous; "
                "use on_startup() for async setup"
            )
        return plugin

    def include_router(self, router, prefix=""):
        self.router.include(router, prefix=prefix)

    def add_service(self, name, service):
        self.state[name] = service
        return service

    def get_service(self, name, default=None):
        return self.state.get(name, default)

    def on_startup(self, func):
        return self.lifecycle.on_startup(func)

    def on_shutdown(self, func):
        return self.lifecycle.on_shutdown(func)

    def add_exception_handler(self, exc_class, handler):
        self._exception_handlers[exc_class] = handler
        return handler

    # -- route shortcuts --------------------------------------------------
    def route(self, path=None, methods=None, name=None):
        return self.router.route(path, methods=methods, name=name)

    def get(self, path=None, name=None):
        return self.router.get(path, name=name)

    def post(self, path=None, name=None):
        return self.router.post(path, name=name)

    def put(self, path=None, name=None):
        return self.router.put(path, name=name)

    def patch(self, path=None, name=None):
        return self.router.patch(path, name=name)

    def delete(self, path=None, name=None):
        return self.router.delete(path, name=name)

    def head(self, path=None, name=None):
        return self.router.head(path, name=name)

    def options(self, path=None, name=None):
        return self.router.options(path, name=name)

    # -- ASGI ---------------------------------------------------------------
    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
        elif scope["type"] == "http":
            request = Request(scope, receive)
            request.app = self
            try:
                response = await self._run_pipeline(request)
            except Exception as exc:  # never leak a traceback to the client
                response = self._error_response(request, exc)
            await response(scope, receive, send)
        else:  # pragma: no cover - non-http scopes
            response = JSONResponse({"error": f"Unsupported scope type: {scope['type']}"}, 500)
            await response(scope, receive, send)

    async def _handle_lifespan(self, scope, receive, send):
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    await self.startup()
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                try:
                    await self.shutdown()
                except Exception as exc:
                    await send({"type": "lifespan.shutdown.failed", "message": str(exc)})
                else:
                    await send({"type": "lifespan.shutdown.complete"})
                return

    async def startup(self):
        await self.plugins.run_startup(self)
        await self.lifecycle.run_startup()

    async def shutdown(self):
        await self.lifecycle.run_shutdown()
        await self.plugins.run_shutdown(self)

    # -- request pipeline -----------------------------------------------------
    async def _run_pipeline(self, request):
        async def run(index, req):
            if index >= len(self._middleware):
                return await self._dispatch(req)
            middleware = self._middleware[index]

            async def call_next(next_req=None):
                return await run(index + 1, next_req or req)

            result = middleware(req, call_next)
            return await _await_value(result)

        return await run(0, request)

    async def _dispatch(self, request):
        handler, match = self.router.match(request.method, request.path)
        if handler is None:
            allowed = (match or {}).get("_allowed", set())
            if allowed:
                raise MethodNotAllowed(
                    f"Method {request.method} not allowed",
                    headers=[("allow", ", ".join(sorted(allowed)))],
                )
            raise NotFound(f"Route {request.path} not found")
        request.path_params = match
        result = await self._await_result(handler(request))
        return self._coerce_response(result)

    @staticmethod
    async def _await_result(result):
        if inspect.isawaitable(result):
            return await result
        return result

    @staticmethod
    def _coerce_response(result):
        if result is None:
            return Response(b"", status_code=204)
        if isinstance(result, Response):
            return result
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
            return _tuple_response(result[0], result[1])
        if isinstance(result, (dict, list)):
            return JSONResponse(result)
        if isinstance(result, (bytes, bytearray)):
            return Response(bytes(result), media_type="application/octet-stream")
        return Response(str(result))

    # -- errors -----------------------------------------------------------------
    def _error_response(self, request, exc):
        for exc_class, handler in self._exception_handlers.items():
            try:
                if isinstance(exc, exc_class):
                    result = handler(request, exc)
                    if inspect.isawaitable(result):  # pragma: no cover
                        raise RuntimeError("Exception handlers must be synchronous")
                    return self._coerce_response(result)
            except Exception:
                continue
        if isinstance(exc, HTTPException):
            return JSONResponse({"error": exc.detail}, status_code=exc.status_code,
                                headers=exc.headers or None)
        detail = str(exc) if self.settings.get("DEBUG") else "Internal Server Error"
        return JSONResponse({"error": detail}, status_code=500)

    # -- serving ------------------------------------------------------------------
    def run(self, host=None, port=None, **uvicorn_kwargs):
        """Serve with Uvicorn (the Phase-1 ASGI server)."""
        import uvicorn

        uvicorn.run(
            self,
            host=host or self.settings.get("HOST"),
            port=port or self.settings.get("PORT"),
            log_level=self.settings.get("LOG_LEVEL"),
            **uvicorn_kwargs,
        )


def _tuple_response(body, status):
    if isinstance(body, (dict, list)):
        return JSONResponse(body, status_code=status)
    if isinstance(body, Response):
        body.status_code = status
        return body
    if isinstance(body, (bytes, bytearray)):
        return Response(bytes(body), status_code=status, media_type="application/octet-stream")
    return Response(str(body), status_code=status)
