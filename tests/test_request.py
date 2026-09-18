from meraki.core.request import Request

def test_request_initialization():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/users",
        "headers": [(b"host", b"localhost"), (b"accept", b"application/json"), (b"accept", b"text/html")],
        "query_string": b"foo=bar&baz=1"
    }
    req = Request(scope)
    assert req.method == "POST"
    assert req.path == "/users"
    assert len(req.headers) == 3
    assert req.headers[0] == (b"host", b"localhost")
    assert req.query_params == [("foo", "bar"), ("baz", "1")]

def test_request_empty_scope():
    scope = {"type": "http"}
    req = Request(scope)
    
    assert req.method == ""
    assert req.path == ""
    assert req.headers == []
    assert req.query_params == []
