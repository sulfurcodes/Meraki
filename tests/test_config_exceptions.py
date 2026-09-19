import json
import os

from meraki import Meraki, Settings
from meraki.exceptions import (
    BadRequest,
    HTTPException,
    InternalServerError,
    NotFound,
)
from tests.helpers import call_app


def test_settings_defaults_overrides_env():
    s = Settings()
    assert s.get("HOST") == "127.0.0.1" and s.get("PORT") == 8000
    assert s["DEBUG"] is False

    s2 = Settings(port=9000, custom_flag=True)
    assert s2["PORT"] == 9000 and s2["CUSTOM_FLAG"] is True

    os.environ["MERAKI_PORT"] = "1234"
    try:
        assert Settings()["PORT"] == 1234
    finally:
        del os.environ["MERAKI_PORT"]


def test_http_exception_mapping_and_custom_handler():
    app = Meraki()

    @app.get("/missing-thing")
    def h(request):
        raise NotFound("no such thing")

    status, _, body = call_app(app, "GET", "/missing-thing")
    assert status == 404
    assert json.loads(body) == {"error": "no such thing"}

    app2 = Meraki()

    @app2.get("/bad")
    def bad(request):
        raise BadRequest("nope")

    app2.add_exception_handler(BadRequest, lambda req, exc: ({"custom": True}, 400))
    status, _, body = call_app(app2, "GET", "/bad")
    assert status == 400
    assert json.loads(body) == {"custom": True}


def test_exception_hierarchy_defaults():
    assert HTTPException().status_code == 500
    assert NotFound().status_code == 404
    assert InternalServerError("x").detail == "x"
