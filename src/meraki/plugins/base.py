"""Plugin interface.

A plugin extends the framework without touching the core by hooking into
the application at registration time and into the lifecycle at
startup/shutdown::

    class AuthPlugin(Plugin):
        name = "auth"

        def register(self, app):
            app.router.get("/me")(self.me)
            app.add_middleware(RequireAuth())

        async def on_startup(self, app):
            app.add_service("users", UserService(app.settings))

        async def on_shutdown(self, app):
            await app.get_service("users").close()
"""

import inspect

from ..exceptions.base import PluginError


class Plugin:
    """Base class for all Meraki plugins."""

    name = "plugin"

    def register(self, app):
        """Wire routes, middleware, config, and services into ``app``."""

    async def on_startup(self, app):
        """Run after registration when the application starts."""

    async def on_shutdown(self, app):
        """Run when the application shuts down."""

    def __repr__(self):  # pragma: no cover - trivial
        return f"{type(self).__name__}(name={self.name!r})"


def _is_plugin_class(obj):
    return inspect.isclass(obj) and issubclass(obj, Plugin)


def coerce_plugin(plugin_like):
    """Accept a ``Plugin`` instance or subclass and return an instance."""
    if isinstance(plugin_like, Plugin):
        return plugin_like
    if _is_plugin_class(plugin_like):
        return plugin_like()
    raise PluginError(
        f"Plugins must be Plugin instances or subclasses, got {plugin_like!r}"
    )
