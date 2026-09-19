"""PostgreSQL connector (requires ``pip install meraki[postgres]`` → asyncpg)."""

from ..interfaces.db_connector import DatabaseConnector

_DRIVER_HINT = "PostgreSQL support needs the 'asyncpg' package: pip install meraki[postgres]"


def _to_dicts(records):
    return [dict(record) for record in records]


class PostgreSQLConnector(DatabaseConnector):
    def __init__(self, dsn=None, *, host="localhost", port=5432,
                 user=None, password=None, database=None, **options):
        super().__init__(connection_string=dsn, **options)
        self.dsn = dsn
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._conn = None

    @property
    def dialect(self):
        return "postgresql"

    @property
    def is_connected(self):
        return self._conn is not None

    def _require_driver(self):
        try:
            import asyncpg  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(_DRIVER_HINT) from exc
        return __import__("asyncpg")

    async def connect(self):
        if self._conn is not None:
            return
        asyncpg = self._require_driver()
        kwargs = dict(self.options)
        if self.dsn:
            self._conn = await asyncpg.connect(self.dsn, **kwargs)
        else:
            self._conn = await asyncpg.connect(
                host=self.host, port=self.port, user=self.user,
                password=self.password, database=self.database, **kwargs
            )

    async def disconnect(self):
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        await conn.close()

    async def _ensure(self):
        if self._conn is None:
            await self.connect()
        return self._conn

    async def execute(self, query, params=None):
        conn = await self._ensure()
        return await conn.execute(query, *(params or ()))

    async def fetch_one(self, query, params=None):
        conn = await self._ensure()
        row = await conn.fetchrow(query, *(params or ()))
        return dict(row) if row is not None else None

    async def fetch_all(self, query, params=None):
        conn = await self._ensure()
        return _to_dicts(await conn.fetch(query, *(params or ())))
