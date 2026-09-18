import urllib.parse
from typing import List, Tuple

class Request:
    """
    A minimal abstraction around an ASGI HTTP scope.
    """
    def __init__(self, scope: dict) -> None:
        self._scope = scope
        self.method: str = scope.get("method", "")
        self.path: str = scope.get("path", "")
        
        # Headers are retained as a list of byte pairs as defined by ASGI,
        # preserving potential duplicate header keys.
        self.headers: List[Tuple[bytes, bytes]] = scope.get("headers", [])
        
        # Parse ASGI query_string into list of tuples
        query_string = scope.get("query_string", b"").decode("latin-1")
        self.query_params: List[Tuple[str, str]] = urllib.parse.parse_qsl(query_string)
