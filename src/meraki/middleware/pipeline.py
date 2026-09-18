from typing import Callable, List, Awaitable
from meraki.core.request import Request
from meraki.core.response import Response

# Signature: async def mw(request, call_next) -> Response
MiddlewareCallable = Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]

class MiddlewarePipeline:
    """
    Manages the sequential execution of registered middleware layers wrapping application routing.
    """
    def __init__(self) -> None:
        self.middlewares: List[MiddlewareCallable] = []

    def add(self, middleware: MiddlewareCallable) -> None:
        """Register a new middleware stage."""
        self.middlewares.append(middleware)

    async def execute(self, request: Request, final_handler: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Executes the provided middlewares correctly layered. Request transitions 'inward', Response transits 'outward'.
        """
        chain = final_handler
        
        for mw in reversed(self.middlewares):
            chain = self._make_next_layer(mw, chain)
            
        return await chain(request)

    def _make_next_layer(self, mw: MiddlewareCallable, next_chain: Callable[[Request], Awaitable[Response]]) -> Callable[[Request], Awaitable[Response]]:
        async def layer(req: Request) -> Response:
            return await mw(req, next_chain)
        return layer
