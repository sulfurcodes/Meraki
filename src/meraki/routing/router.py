"""Path-based router.

Supported parameter styles (fully stdlib, no extra dependencies)::

    /users/{id}            str
    /users/{id:int}        int (\\d+)
    /users/{score:float}   float
    /users/{file:path}     str incl. slashes
    /users/{uid:uuid}      str, uuid-shaped
    /users/:id  /users/<id>  /users/<int:id>   (legacy aliases)
"""

import re
import uuid as _uuid

_CONVERTERS = {
    "str": (r"[^/]+", str),
    "int": (r"\d+", int),
    "float": (r"\d+(?:\.\d+)?", float),
    "path": (r".+", str),
    "uuid": (r"[0-9a-fA-F-]{36}", str),
}

# Single-pass pattern for all param styles. One pass is essential: staged
# substitutions would match alias syntax inside already-generated (?P<...>)
# groups (e.g. `<name>` in `(?P<name>...)`, or `:int` in `{n:int}`).
# Groups: 1=name{brace} 2=kind{brace} 3=kind<angle> 4=name<angle> 5=name:colon
_PARAM_PATTERN = re.compile(
    r"\{(\w+)(?::(\w+))?\}|<(?:(int|float|path|uuid|str):)?(\w+)>|:(\w+)"
)

_ALL_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")


def _compile(template):
    converters = {}

    def param_repl(match):
        if match.group(1) is not None:  # {name} / {name:kind}
            name, kind = match.group(1), (match.group(2) or "str").lower()
        elif match.group(4) is not None:  # <name> / <kind:name>
            name, kind = match.group(4), (match.group(3) or "str").lower()
        else:  # :name
            name, kind = match.group(5), "str"
        pattern, caster = _CONVERTERS.get(kind, _CONVERTERS["str"])
        converters[name] = caster
        return f"(?P<{name}>{pattern})"

    regex = _PARAM_PATTERN.sub(param_repl, template)
    if template == "/":
        return re.compile(r"^/?$"), {}
    return re.compile(f"^{regex.rstrip('/') or '/'}/?$"), converters


class Route:
    __slots__ = ("template", "methods", "handler", "name", "regex", "converters")

    def __init__(self, template, methods, handler, name=None):
        self.template = template
        self.methods = {m.upper() for m in methods}
        self.handler = handler
        self.name = name or getattr(handler, "__name__", template)
        self.regex, self.converters = _compile(template)


class Router:
    def __init__(self):
        self._routes = []

    # -- registration --
    def add(self, path, handler, methods, name=None):
        template = path or f"/{getattr(handler, '__name__', 'route')}"
        route = Route(template, methods, handler, name=name)
        self._routes.append(route)
        return handler

    def route(self, path=None, methods=None, name=None):
        methods = [m.upper() for m in (methods or ["GET"])]

        def wrapper(handler):
            return self.add(path, handler, methods, name=name)

        return wrapper

    def get(self, path=None, name=None):
        return self.route(path, methods=["GET"], name=name)

    def post(self, path=None, name=None):
        return self.route(path, methods=["POST"], name=name)

    def put(self, path=None, name=None):
        return self.route(path, methods=["PUT"], name=name)

    def patch(self, path=None, name=None):
        return self.route(path, methods=["PATCH"], name=name)

    def delete(self, path=None, name=None):
        return self.route(path, methods=["DELETE"], name=name)

    def head(self, path=None, name=None):
        return self.route(path, methods=["HEAD"], name=name)

    def options(self, path=None, name=None):
        return self.route(path, methods=["OPTIONS"], name=name)

    def include(self, other, prefix=""):
        """Mount another router under a path prefix."""
        for route in other._routes:
            template = prefix.rstrip("/") + route.template
            self._routes.append(Route(template, route.methods, route.handler, route.name))

    # -- matching --
    def match(self, method, path):
        """Return ``(handler, path_params)`` or ``(None, {"_allowed": {...}})``."""
        if not path:
            path = "/"
        method = method.upper()
        allowed = set()
        for route in self._routes:
            match = route.regex.match(path)
            if not match:
                continue
            allowed.update(route.methods)
            if method in route.methods or (method == "HEAD" and "GET" in route.methods):
                params = {}
                valid = True
                for key, value in match.groupdict().items():
                    caster = route.converters.get(key, str)
                    try:
                        if caster is str and self._is_uuid_param(route.template, key):
                            _uuid.UUID(str(value))  # strict uuid validation
                        params[key] = caster(value)
                    except (ValueError, TypeError, AttributeError):
                        valid = False
                        break
                if valid:
                    return route.handler, params
        return None, {"_allowed": allowed} if allowed else {}

    @staticmethod
    def _is_uuid_param(template, key):
        return f"{key}:uuid" in template or f"<uuid:{key}>" in template

    @property
    def routes(self):
        return list(self._routes)

    def __len__(self):
        return len(self._routes)
