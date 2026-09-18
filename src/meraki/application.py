from typing import Callable
from meraki.core.request import Request
from meraki.core.response import Response
from meraki.routing.router import Router
from meraki.middleware.pipeline import MiddlewarePipeline

class Meraki:
    """
    The central application object for the Meraki backend framework.
    """
    
    def __init__(self) -> None:
        self.router = Router()
        self.pipeline = MiddlewarePipeline()

    def add_middleware(self, middleware: Callable) -> None:
        """Register a middleware callable."""
        self.pipeline.add(middleware)

    def get(self, path: str) -> Callable:
        return self.router.get(path)

    def post(self, path: str) -> Callable:
        return self.router.post(path)

    def put(self, path: str) -> Callable:
        return self.router.put(path)

    def delete(self, path: str) -> Callable:
        return self.router.delete(path)

    def patch(self, path: str) -> Callable:
        return self.router.patch(path)

    async def __call__(self, scope: dict, receive, send) -> None:
        """
        The main ASGI entrypoint. Process incoming connections.
        """
        scope_type = scope["type"]

        if scope_type == "http":
            await self._handle_http_request(scope, receive, send)
        elif scope_type == "lifespan":
            # For Uvicorn lifespan handling (startup/shutdown)
            await self._handle_lifespan(scope, receive, send)
        else:
            raise NotImplementedError(f"Scope type '{scope_type}' is not supported.")

    async def _handle_http_request(self, scope: dict, receive, send) -> None:
        """
        Handle ASGI HTTP requests, sending them through the middleware pipeline
        before dispatching to the router.
        """
        request = Request(scope)
        
        async def final_stage(req: Request) -> Response:
            handler, error = self.router.match(req)
            
            if error == 404:
                return Response(status_code=404, body=b"Not Found")
            elif error == 405:
                return Response(status_code=405, body=b"Method Not Allowed")
            else:
                return await handler(req)
                
        # Connect pipeline flow
        response = await self.pipeline.execute(request, final_stage)
            
        await response.send(send)

    async def _handle_lifespan(self, scope: dict, receive, send) -> None:
        """
        Handle ASGI lifespan events (startup/shutdown).
        """
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
