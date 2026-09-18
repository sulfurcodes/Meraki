import pytest
import httpx
from httpx import ASGITransport

from meraki import Meraki


def test_meraki_can_be_imported():
    """Verify that Meraki is exposed at the package root."""
    assert Meraki is not None


def test_meraki_app_instantiation():
    """Verify that the Meraki application can be instantiated."""
    app = Meraki()
    assert isinstance(app, Meraki)


@pytest.mark.asyncio
async def test_meraki_asgi_callable():
    """Verify that the Meraki application handles invalid ASGI scopes."""
    app = Meraki()
    
    with pytest.raises(NotImplementedError, match="Scope type 'unknown' is not supported."):
        await app({"type": "unknown"}, receive=None, send=None)


@pytest.mark.asyncio
async def test_meraki_http_request():
    """
    Verify that a basic HTTP request to the Meraki application returns a valid response
    when routed through the Router correctly.
    """
    app = Meraki()
    
    @app.get("/")
    async def home(request):
        from meraki.core.response import Response
        return Response(body=b"Hello from Meraki!")
    
    # We use httpx ASGITransport to bypass the need for a real HTTP server (like uvicorn).
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/")
        
        assert response.status_code == 200
        assert response.text == "Hello from Meraki!"
        assert response.headers["content-type"] == "text/plain"

        # Test 404 Not Found
        response_404 = await client.get("/missing")
        assert response_404.status_code == 404
        assert response_404.text == "Not Found"

        # Test 405 Method Not Allowed
        response_405 = await client.post("/")
        assert response_405.status_code == 405
        assert response_405.text == "Method Not Allowed"
