"""Framework-level exceptions.

All HTTP-aware errors derive from :class:`HTTPException`, which the
application core translates into JSON responses. Plain (non-HTTP)
exceptions become ``500 Internal Server Error``.
"""


class MerakiException(Exception):
    """Base class for all Meraki errors."""


class HTTPException(MerakiException):
    """An error that maps directly to an HTTP response."""

    status_code = 500
    detail = "Internal Server Error"

    def __init__(self, detail=None, status_code=None, headers=None):
        super().__init__(detail or self.detail)
        if status_code is not None:
            self.status_code = int(status_code)
        if detail is not None:
            self.detail = str(detail)
        self.headers = list(headers) if headers else []

    def __str__(self):  # pragma: no cover - trivial
        return f"{self.status_code}: {self.detail}"


class BadRequest(HTTPException):
    status_code = 400
    detail = "Bad Request"


class Unauthorized(HTTPException):
    status_code = 401
    detail = "Unauthorized"


class Forbidden(HTTPException):
    status_code = 403
    detail = "Forbidden"


class NotFound(HTTPException):
    status_code = 404
    detail = "Not Found"


class MethodNotAllowed(HTTPException):
    status_code = 405
    detail = "Method Not Allowed"


class UnprocessableEntity(HTTPException):
    status_code = 422
    detail = "Unprocessable Entity"


class InternalServerError(HTTPException):
    status_code = 500
    detail = "Internal Server Error"


class ConfigurationError(MerakiException):
    """Raised when framework or plugin configuration is invalid."""


class PluginError(MerakiException):
    """Raised for plugin registration / lifecycle failures."""
