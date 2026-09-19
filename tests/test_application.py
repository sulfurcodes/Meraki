import json

from meraki import Meraki
from tests.helpers import call_app


def make_app():
    app = Meraki()

    @app.get("/hello")
    def hello(request):
        return {"message": "hi"}

    @app.get("/users/{id:int}")
    def get_user(request):
        return {"id": request.path_params["id"]}

    @app.post("/echo")
    async def echo(request):
        return {"you_sent": await request.json()}

    @app.get("/boom")
    def boom(request):
        raise ValueError("kaboom")

    return app


def test_basic_route():
    status, _, body = call_app(make_app(), "GET", "/hello")
    assert status == 200
    assert json.loads(body) == {"message": "hi"}


def test_path_params_int_coerced():
    status, _, body = call_app(make_app(), "GET", "/users/42")
    assert status == 200
    assert json.loads(body) == {"id": 42}


def test_unmatched_route_404():
    status, _, body = call_app(make_app(), "GET", "/nope")
    assert status == 404
    assert "error" in json.loads(body)


def test_wrong_method_405_with_allow_header():
    status, headers, body = call_app(make_app(), "DELETE", "/hello")
    assert status == 405
    assert "GET" in headers.get("allow", "")
    assert "error" in json.loads(body)


def test_post_json_body():
    status, _, body = call_app(make_app(), "POST", "/echo", body={"a": 1})
    assert status == 200
    assert json.loads(body) == {"you_sent": {"a": 1}}


def test_unhandled_error_is_500_without_leak():
    status, _, body = call_app(make_app(), "GET", "/boom")
    assert status == 500
    assert json.loads(body) == {"error": "Internal Server Error"}


def test_debug_shows_detail():
    app = make_app()
    app.settings.set("DEBUG", True)
    status, _, body = call_app(app, "GET", "/boom")
    assert status == 500
    assert json.loads(body)["error"] == "kaboom"


def test_head_falls_back_to_get():
    status, _, _ = call_app(make_app(), "HEAD", "/hello")
    assert status == 200
