from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # Avoid circular import at runtime.
    from meraki.application import Meraki


class Plugin:
    """
    Base class for Meraki plugins.

    A plugin extends the framework without modifying the core by:

    - registering routes / middleware via ``register(app)``
    - exposing shared objects via services (``app.add_service``)
    - hooking into startup/shutdown via ``on_startup`` / ``on_shutdown``

    Subclasses should set a unique ``name`` and override ``register``.
    ``on_startup`` / ``on_shutdown`` may be sync or async.
    """

    name: str = "plugin"

    def register(self, app: Meraki) -> None:
        """Called once when the plugin is registered on the app."""
        return None

    def on_startup(self) -> None:
        """Called during ASGI lifespan startup. May be sync or async."""
        return None

    def on_shutdown(self) -> None:
        """Called during ASGI lifespan shutdown. May be sync or async."""
        return None
