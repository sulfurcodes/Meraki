"""MySQL connector (requires ``pip install meraki[mysql]`` → aiomysql)."""

from ..interfaces.db_connector import DatabaseConnector

_DRIVER_HINT = "MySQL support needs the 'aiomysql' package: pip install meraki[mysql]"


class MySQLConnector(DatabaseConnector):
    def __init__(self, *, host="localhost", port=3306, user=None,
                 password=None, database=None, **options):
        super().__init__(connection_string=None, **options)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self._pool = None

    @property
    def dialect(self):
        return "mysql"

    @property
    def is_connected(self):
        return self._pool is not None

    def _require_driver(self):
        try:
            import aiomysql  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(_DRIVER_HINT) from exc
        return __import__("aiomysql")

    async def connect(self):
        if self._pool is not None:
            return
        aiomysql = self._require_driver()
        self._pool = await aiomysql.create_pool(
            host=self.host, port=self.port, user=self.user,
            password=self.password, db=self.database, **self.options
        )

    async def disconnect(self):
        if self._pool is None:
            return
        pool, self._pool = self._pool, None
        pool.close()
        await pool.wait_closed()

    async def _cursor(self):
        if self._pool is None:
            await self.connect()
        return self._pool.acquire()

    async def execute(self, query, params=None):
        from aiomysql.cursors import DictCursor  # local import: driver required
        async with await self._cursor() as conn:
            async with conn.cursor(DictCursor) as cur:
                affected = await cur.execute(query, params or ())
                await conn.commit()
                return cur.lastrowid or affected

    async def fetch_one(self, query, params=None):
        from aiomysql.cursors import DictCursor
        async with await self._cursor() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(query, params or ())
                return await cur.fetchone()

    async def fetch_all(self, query, params=None):
        from aiomysql.cursors import DictCursor
        async with await self._cursor() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(query, params or ())
                return list(await cur.fetchall())
