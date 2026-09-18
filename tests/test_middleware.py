import pytest
from httpx import ASGITransport, AsyncClient
from meraki import Meraki
from meraki.core.response import Response

@pytest.mark.asyncio
async def test_middleware_order_and_modification():
    """Verify middleware executes in the correct nested order, and can modify both incoming Requests and outgoing Responses."""
    app = Meraki()
    
    order = []
    
    async def middleware_a(req, call_next):
        order.append("A_pre")
        res = await call_next(req)
        order.append("A_post")
        res.headers.append((b"x-middleware-a", b"true"))
        return res
        
    async def middleware_b(req, call_next):
        order.append("B_pre")
        req.path = "/modified/path"
        res = await call_next(req)
        order.append("B_post")
        res.headers.append((b"x-middleware-b", b"true"))
        return res
        
    app.add_middleware(middleware_a)
    app.add_middleware(middleware_b)
    
    @app.get("/modified/path")
    async def handler(req):
        order.append("handler")
        return Response(body=b"OK")
        
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Standard route should fail if not modified, since registered is "/modified/path"
        res = await client.get("/initial")
        
        assert res.status_code == 200
        assert order == ["A_pre", "B_pre", "handler", "B_post", "A_post"]
        
        # Test Headers manipulation bubble back properly
        assert "x-middleware-a" in res.headers
        assert "x-middleware-b" in res.headers

@pytest.mark.asyncio
async def test_middleware_terminal_response():
    """Verify middleware can return a Response early bypassing final stages successfully."""
    app = Meraki()
    
    async def block_mw(req, call_next):
        return Response(status_code=403, body=b"Forbidden")
        
    app.add_middleware(block_mw)
    
    @app.get("/")
    async def home(req):
        return Response(body=b"OK")
        
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        res = await client.get("/")
        
        assert res.status_code == 403
        assert res.text == "Forbidden"
