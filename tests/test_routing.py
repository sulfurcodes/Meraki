from meraki.routing import Router


def test_str_and_alias_styles():
    r = Router()
    r.get("/a/{name}")(lambda req: None)
    r.get("/b/:name")(lambda req: None)
    r.get("/c/<name>")(lambda req: None)
    for path in ("/a/x", "/b/x", "/c/x"):
        handler, params = r.match("GET", path)
        assert handler is not None
        assert params == {"name": "x"}


def test_converters():
    r = Router()

    @r.get("/i/{n:int}")
    def h(req):
        pass

    handler, params = r.match("GET", "/i/7")
    assert params == {"n": 7} and isinstance(params["n"], int)

    @r.get("/f/{n:float}")
    def h2(req):
        pass

    _, params = r.match("GET", "/f/2.5")
    assert params == {"n": 2.5}

    @r.get("/rest/{p:path}")
    def h3(req):
        pass

    _, params = r.match("GET", "/rest/a/b/c")
    assert params == {"p": "a/b/c"}


def test_uuid_strict():
    import uuid as _uuid
    r = Router()

    @r.get("/u/{uid:uuid}")
    def h(req):
        pass

    good = str(_uuid.uuid4())
    handler, params = r.match("GET", f"/u/{good}")
    assert handler is not None and params == {"uid": good}
    handler, _ = r.match("GET", "/u/not-a-uuid")
    assert handler is None


def test_405_reports_allowed():
    r = Router()
    r.get("/x")(lambda req: None)
    r.post("/x")(lambda req: None)
    handler, match = r.match("DELETE", "/x")
    assert handler is None
    assert match["_allowed"] == {"GET", "POST"}


def test_trailing_slash_and_root():
    r = Router()
    r.get("/")(lambda req: None)
    r.get("/items")(lambda req: None)
    assert r.match("GET", "/")[0] is not None
    assert r.match("GET", "/items/")[0] is not None


def test_include_prefix():
    sub = Router()
    sub.get("/list")(lambda req: None)
    main = Router()
    main.include(sub, prefix="/api")
    handler, _ = main.match("GET", "/api/list")
    assert handler is not None
