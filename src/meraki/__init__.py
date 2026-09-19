"""Meraki — modular, plugin-based Python backend framework."""

from .application import Meraki
from .config.settings import Settings
from .core.request import Request
from .core.response import Response, JSONResponse, PlainTextResponse, HTMLResponse
from .exceptions.base import (
    MerakiException,
    HTTPException,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    MethodNotAllowed,
    UnprocessableEntity,
    InternalServerError,
    ConfigurationError,
    PluginError,
)
from .middleware.pipeline import (
    BaseMiddleware,
    LoggerMiddleware,
    CORSMiddleware,
    TrustedHostMiddleware,
)
from .plugins.base import Plugin
from .plugins.manager import PluginManager
from .routing.router import Router

__version__ = "0.1.0"

__all__ = [
    "Meraki",
    "Settings",
    "Request",
    "Response",
    "JSONResponse",
    "PlainTextResponse",
    "HTMLResponse",
    "Router",
    "Plugin",
    "PluginManager",
    "BaseMiddleware",
    "LoggerMiddleware",
    "CORSMiddleware",
    "TrustedHostMiddleware",
    "MerakiException",
    "HTTPException",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "NotFound",
    "MethodNotAllowed",
    "UnprocessableEntity",
    "InternalServerError",
    "ConfigurationError",
    "PluginError",
]
