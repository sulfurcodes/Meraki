from typing import List, Tuple, Optional

class Response:
    """
    A minimal HTTP Response abstraction.
    """
    def __init__(self, body: bytes = b"", status_code: int = 200, headers: Optional[List[Tuple[bytes, bytes]]] = None) -> None:
        self.body = body
        self.status_code = status_code
        if headers is None:
            self.headers: List[Tuple[bytes, bytes]] = [
                (b"content-type", b"text/plain"),
                (b"content-length", str(len(body)).encode("latin-1")),
            ]
        else:
            self.headers = headers

    async def send(self, send_callable) -> None:
        """
        Translates the Request state into ASGI messages and sends them via the ASGI send callable.
        """
        await send_callable({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.headers,
        })
        await send_callable({
            "type": "http.response.body",
            "body": getattr(self, "body", b""),
        })
