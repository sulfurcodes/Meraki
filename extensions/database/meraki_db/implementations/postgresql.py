import re
from typing import Any, Dict, List, Optional
import asyncpg
from meraki_db.interfaces.connector import DatabaseConnector

class PostgreSQLConnector(DatabaseConnector):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5432,
        user: str = "postgres",
        password: str = "",
        database: str = "postgres",
        dsn: Optional[str] = None
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self.pool is not None:
            return

        if self.dsn:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        else:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )

    async def disconnect(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    def _get_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("Database connection pool is not initialized. Call connect() first.")
        return self.pool

    def _prepare_query(self, query: str, params: Optional[Dict[str, Any]]) -> tuple[str, list[Any]]:
        if not params:
            return query, []
            
        positional_args = []
        distinct_params: Dict[str, int] = {}
        
        def replacer(match: re.Match) -> str:
            name = match.group(1)
            if name in params:
                if name not in distinct_params:
                    distinct_params[name] = len(distinct_params) + 1
                    positional_args.append(params[name])
                return f"${distinct_params[name]}"
            return match.group(0)
            
        new_query = re.sub(r':([a-zA-Z0-9_]+)', replacer, query)
        return new_query, positional_args

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        pool = self._get_pool()
        new_query, args = self._prepare_query(query, params)
        async with pool.acquire() as conn:
            return await conn.execute(new_query, *args)

    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        pool = self._get_pool()
        new_query, args = self._prepare_query(query, params)
        async with pool.acquire() as conn:
            row = await conn.fetchrow(new_query, *args)
            if row is not None:
                return dict(row)
            return None

    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pool = self._get_pool()
        new_query, args = self._prepare_query(query, params)
        async with pool.acquire() as conn:
            rows = await conn.fetch(new_query, *args)
            return [dict(row) for row in rows]
