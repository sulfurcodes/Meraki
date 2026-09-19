"""SQLite connector — stdlib only, no extra install needed."""

import asyncio
import sqlite3

from ..interfaces.db_connector import DatabaseConnector


class SQLiteConnector(DatabaseConnector):
    """SQLite via the standard library (blocking calls run in a thread)."""

    def __init__(self, db_path=":memory:", **options):
        super().__init__(connection_string=db_path, **options)
        self.db_path = db_path
        self._conn = None
        self._lock = asyncio.Lock()

    @property
    def dialect(self):
        return "sqlite"

    @property
    def is_connected(self):
        return self._conn is not None

    async def connect(self):
        if self._conn is not None:
            return
        def _open():
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        self._conn = await asyncio.to_thread(_open)

    async def disconnect(self):
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        await asyncio.to_thread(conn.close)

    async def _run(self, query, params=None, mode="execute"):
        if self._conn is None:
            await self.connect()
        params = params or ()

        def _op():
            cur = self._conn.execute(query, params)
            if mode == "execute":
                self._conn.commit()
                return cur.lastrowid if cur.lastrowid else cur.rowcount
            if mode == "one":
                row = cur.fetchone()
                return dict(row) if row is not None else None
            return [dict(row) for row in cur.fetchall()]

        async with self._lock:
            return await asyncio.to_thread(_op)

    async def execute(self, query, params=None):
        return await self._run(query, params, mode="execute")

    async def fetch_one(self, query, params=None):
        return await self._run(query, params, mode="one")

    async def fetch_all(self, query, params=None):
        return await self._run(query, params, mode="all")
