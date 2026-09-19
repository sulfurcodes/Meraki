"""Application lifecycle (startup / shutdown)."""

import inspect


async def _maybe_await(func, *args, **kwargs):
    result = func(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class Lifecycle:
    """Holds startup/shutdown handlers run around the serving lifetime."""

    def __init__(self):
        self._startup = []
        self._shutdown = []

    def on_startup(self, func):
        self._startup.append(func)
        return func

    def on_shutdown(self, func):
        self._shutdown.append(func)
        return func

    @property
    def startup_handlers(self):
        return list(self._startup)

    @property
    def shutdown_handlers(self):
        return list(self._shutdown)

    async def run_startup(self):
        for handler in self._startup:
            await _maybe_await(handler)

    async def run_shutdown(self):
        for handler in reversed(self._shutdown):
            await _maybe_await(handler)
