"""Centralized configuration.

``Settings`` holds framework, application, and extension settings in one
place so components never reach into each other's config. Values can come
from defaults, ``MERAKI_``-prefixed environment variables, or explicit
keyword overrides (highest precedence).
"""

import os

DEFAULTS = {
    "DEBUG": False,
    "TITLE": "Meraki",
    "HOST": "127.0.0.1",
    "PORT": 8000,
    "LOG_LEVEL": "info",
    "ALLOWED_HOSTS": ["*"],
    "CORS_ALLOW_ORIGINS": ["*"],
    "CORS_ALLOW_METHODS": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    "CORS_ALLOW_HEADERS": ["Content-Type", "Authorization"],
    "DATABASE_URL": None,
}

_ENV_PREFIX = "MERAKI_"


def _coerce(value, reference):
    """Coerce an env string to the type of the existing default."""
    if isinstance(reference, bool):
        return value.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(reference, int):
        try:
            return int(value)
        except ValueError:
            return value
    if isinstance(reference, float):
        try:
            return float(value)
        except ValueError:
            return value
    if isinstance(reference, list):
        return [item.strip() for item in value.split(",") if item.strip()]
    return value


class Settings:
    def __init__(self, **overrides):
        self._store = dict(DEFAULTS)
        self._load_env()
        self.update(**overrides)

    def _load_env(self):
        for key in list(self._store.keys()):
            env_key = _ENV_PREFIX + key
            if env_key in os.environ:
                self._store[key] = _coerce(os.environ[env_key], self._store[key])

    def get(self, key, default=None):
        return self._store.get(key, default)

    def set(self, key, value):
        self._store[key] = value

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self._store[key.upper()] = value

    def to_dict(self):
        return dict(self._store)

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        self._store[key] = value

    def __contains__(self, key):
        return key in self._store

    def __repr__(self):  # pragma: no cover - trivial
        return f"Settings({self._store!r})"
