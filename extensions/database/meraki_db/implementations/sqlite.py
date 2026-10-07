import aiosqlite
from typing import Any,Dict,Tuple,Optional,Sequence,List
from meraki_db.interfaces.connector import DatabaseConnector

class SQLiteConnector(DatabaseConnector):
    def __init__(self,database: str = ":memory:", **kwargs: Any) -> None:
        self.database: str = database
        self.options: Dict[str, Any] = kwargs
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.database, **self.options)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON;")
            await self._connection.commit()

    async def disconnect(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def execute(self, query: str, parameters: Optional[Sequence[Any]] = None) -> Any:
        if self._connection is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
        
        async with self._connection.cursor() as cursor:
            if parameters:
                await cursor.execute(query, parameters)
            else:
                await cursor.execute(query)
            await self._connection.commit()
            return cursor.rowcount

    async def fetch_one(self, query: str, parameters: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
        if self._connection is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
            
        async with self._connection.cursor() as cursor:
            if parameters:
                await cursor.execute(query, parameters)
            else:
                await cursor.execute(query)
            row = await cursor.fetchone()
            return dict(row) if row is not None else None

    async def fetch_all(self, query: str, parameters: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        if self._connection is None:
            raise RuntimeError("Database is not connected. Call connect() first.")
            
        async with self._connection.cursor() as cursor:
            if parameters:
                await cursor.execute(query, parameters)
            else:
                await cursor.execute(query)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]