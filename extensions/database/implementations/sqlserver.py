"""SQL Server connector (requires ``pip install meraki[sqlserver]`` → aioodbc)."""

from ..interfaces.db_connector import DatabaseConnector

_DRIVER_HINT = "SQL Server support needs the 'aioodbc' package: pip install meraki[sqlserver]"


class SQLServerConnector(DatabaseConnector):
    def __init__(self, dsn=None, *, driver="{ODBC Driver 18 for SQL Server}",
                 server="localhost", database=None, user=None,
                 password=None, **options):
        super().__init__(connection_string=dsn, **options)
        self.dsn = dsn or (
            f"DRIVER={driver};SERVER={server};DATABASE={database or 'master'};"
            f"UID={user or ''};PWD={password or ''}"
        )
        self._conn = None

    @property
    def dialect(self):
        return "sqlserver"

    @property
    def is_connected(self):
        return self._conn is not None

    def _require_driver(self):
        try:
            import aioodbc  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(_DRIVER_HINT) from exc
        return __import__("aioodbc")

    async def connect(self):
        if self._conn is not None:
            return
        aioodbc = self._require_driver()
        self._conn = await aioodbc.connect(dsn=self.dsn, **self.options)

    async def disconnect(self):
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        await conn.close()

    async def _ensure(self):
        if self._conn is None:
            await self.connect()
        return self._conn

    @staticmethod
    def _columns(cursor):
        return [col[0] for col in cursor.description] if cursor.description else []

    async def execute(self, query, params=None):
        conn = await self._ensure()
        async with conn.cursor() as cur:
            await cur.execute(query, params or ())
            await conn.commit()
            try:
                return cur.rowcount
            except Exception:
                return 0

    async def fetch_one(self, query, params=None):
        conn = await self._ensure()
        async with conn.cursor() as cur:
            await cur.execute(query, params or ())
            row = await cur.fetchone()
            if row is None:
                return None
            return dict(zip(self._columns(cur), row))

    async def fetch_all(self, query, params=None):
        conn = await self._ensure()
        async with conn.cursor() as cur:
            await cur.execute(query, params or ())
            columns = self._columns(cur)
            return [dict(zip(columns, row)) for row in await cur.fetchall()]
