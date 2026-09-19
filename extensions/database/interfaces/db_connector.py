"""Common database connector interface (Strategy Pattern).

Every SQL implementation — SQLite, PostgreSQL, MySQL, SQL Server —
conforms to :class:`DatabaseConnector` so they stay interchangeable and
the framework core never depends on a specific driver. Rows are returned
as plain ``dict`` objects.
"""

from abc import ABC, abstractmethod


class DatabaseConnector(ABC):
    """Async database connector contract."""

    def __init__(self, connection_string=None, **options):
        self.connection_string = connection_string
        self.options = dict(options)

    @property
    @abstractmethod
    def dialect(self) -> str:
        """Short name: ``'sqlite'``, ``'postgresql'``, ``'mysql'``, ``'sqlserver'``."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Whether there is currently an open connection."""

    @abstractmethod
    async def connect(self):
        """Open the underlying connection (idempotent)."""

    @abstractmethod
    async def disconnect(self):
        """Close the underlying connection (idempotent)."""

    @abstractmethod
    async def execute(self, query, params=None):
        """Run a write query; return the last inserted row id or row count."""

    @abstractmethod
    async def fetch_one(self, query, params=None):
        """Run a read query; return one row ``dict`` or ``None``."""

    @abstractmethod
    async def fetch_all(self, query, params=None):
        """Run a read query; return a list of row ``dict`` objects."""

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc_info):
        await self.disconnect()
        return False
