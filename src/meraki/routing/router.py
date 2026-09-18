from typing import Callable, Optional, Tuple, Dict
from meraki.core.request import Request

class Router:
    """
    A minimal HTTP Router mapping static paths and methods to async handler functions.
    """
    def __init__(self) -> None:
        # Structure: { "/path": { "GET": handler, "POST": handler } }
        self.routes: Dict[str, Dict[str, Callable]] = {}

    def add_route(self, path: str, method: str, handler: Callable) -> None:
        method = method.upper()
        if path not in self.routes:
            self.routes[path] = {}
        self.routes[path][method] = handler

    def get(self, path: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, "GET", handler)
            return handler
        return decorator

    def post(self, path: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, "POST", handler)
            return handler
        return decorator

    def put(self, path: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, "PUT", handler)
            return handler
        return decorator

    def delete(self, path: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, "DELETE", handler)
            return handler
        return decorator

    def patch(self, path: str) -> Callable:
        def decorator(handler: Callable) -> Callable:
            self.add_route(path, "PATCH", handler)
            return handler
        return decorator

    def match(self, request: Request) -> Tuple[Optional[Callable], Optional[int]]:
        """
        Attempts to find a matching route for the specified Request.
        
        Returns:
            (handler, None): If a valid match is found.
            (None, 404): If the route path does not exist.
            (None, 405): If the path exists but the method is not configured for it.
        """
        path = request.path
        method = request.method.upper()

        if path not in self.routes:
            return None, 404
        
        route_methods = self.routes[path]
        if method not in route_methods:
            return None, 405
            
        return route_methods[method], None
