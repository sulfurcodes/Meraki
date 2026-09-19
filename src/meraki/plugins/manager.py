"""Plugin manager: registration, lookup, and lifecycle integration."""

import inspect

from ..exceptions.base import PluginError
from .base import coerce_plugin


async def _await_if_needed(value):
    if inspect.isawaitable(value):
        return await value
    return value


class PluginManager:
    def __init__(self):
        self._plugins = {}

    def register(self, plugin_like):
        plugin = coerce_plugin(plugin_like)
        if plugin.name in self._plugins:
            raise PluginError(f"A plugin named {plugin.name!r} is already registered")
        self._plugins[plugin.name] = plugin
        return plugin

    def get(self, name, default=None):
        return self._plugins.get(name, default)

    def __contains__(self, name):
        return name in self._plugins

    def __len__(self):
        return len(self._plugins)

    def __iter__(self):
        return iter(self._plugins.values())

    @property
    def names(self):
        return list(self._plugins.keys())

    async def run_register(self, app):
        for plugin in self._plugins.values():
            await _await_if_needed(plugin.register(app))

    async def run_startup(self, app):
        for plugin in self._plugins.values():
            await _await_if_needed(plugin.on_startup(app))

    async def run_shutdown(self, app):
        for plugin in reversed(list(self._plugins.values())):
            result = plugin.on_shutdown(app)
            if inspect.isawaitable(result):
                await result
