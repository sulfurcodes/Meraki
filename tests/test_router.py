import pytest
from meraki.core.request import Request
from meraki.routing.router import Router

def test_router_registration_and_matching():
    router = Router()
    
    async def handler_get(req): pass
    async def handler_post(req): pass
    
    router.add_route("/test", "GET", handler_get)
    router.add_route("/test", "POST", handler_post)
    
    req_get = Request({"method": "GET", "path": "/test"})
    req_post = Request({"method": "POST", "path": "/test"})
    req_missing_path = Request({"method": "GET", "path": "/missing"})
    req_missing_method = Request({"method": "PUT", "path": "/test"})
    
    # valid matches
    match_get, err_get = router.match(req_get)
    assert match_get is handler_get
    assert err_get is None
    
    match_post, err_post = router.match(req_post)
    assert match_post is handler_post
    assert err_post is None
    
    # 404 path not registered
    match_404, err_404 = router.match(req_missing_path)
    assert match_404 is None
    assert err_404 == 404
    
    # 405 path registered but unsupported method
    match_405, err_405 = router.match(req_missing_method)
    assert match_405 is None
    assert err_405 == 405

def test_router_decorators():
    router = Router()
    
    @router.get("/home")
    async def get_home(req): pass
    
    @router.post("/items")
    async def post_items(req): pass
    
    req1 = Request({"method": "GET", "path": "/home"})
    req2 = Request({"method": "POST", "path": "/items"})
    
    assert router.match(req1)[0] is get_home
    assert router.match(req2)[0] is post_items
