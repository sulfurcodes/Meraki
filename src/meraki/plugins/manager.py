from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Dict, List

from meraki.plugins.base import Plugin

if TYPE_CHECKING:  # Avoid circular import at runtime.
    from meraki.application import Meraki


async def _maybe_await(func, *args, **kwargs):
    """Call ``func`` and await it only if it returns an awaitable."""
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class PluginManager:
    """
    Keeps track of registered plugins and drives their lifecycle.

    Registration is explicit: ``register(plugin, app)`` stores the plugin
    and immediately calls ``plugin.register(app)`` so routes/middleware
    are available right away. Lifespan events call ``on_startup`` /
    ``on_shutdown`` (shutdown in reverse order).
    """

    def __init__(self) -> None:
        self._plugins: List[Plugin] = []
        self._by_name: Dict[str, Plugin] = {}

    @property
    def plugins(self) -> List[Plugin]:
        return list(self._plugins)

    def register(self, plugin: Plugin, app: Meraki) -> Plugin:
        if not isinstance(plugin, Plugin):
            raise TypeError(
                f"plugin must be an instance of meraki.plugins.Plugin, got {type(plugin).__name__!r}"
            )
        name = getattr(plugin, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError("plugin must define a non-empty string 'name'")
        if name in self._by_name:
            raise ValueError(f"plugin with name {name!r} is already registered")
        self._plugins.append(plugin)
        self._by_name[name] = plugin
        plugin.register(app)
        return plugin

    def get(self, name: str) -> Plugin | None:
        return self._by_name.get(name)

    async def startup(self) -> None:
        for plugin in self._plugins:
            await _maybe_await(plugin.on_startup)

    async def shutdown(self) -> None:
        for plugin in reversed(self._plugins):
            await _maybe_await(plugin.on_shutdown)
