import asyncio
import sys

import pytest

from extensions.database import (
    DatabaseConnector,
    MySQLConnector,
    PostgreSQLConnector,
    SQLiteConnector,
    SQLServerConnector,
)


def test_connector_is_abstract():
    with pytest.raises(TypeError):
        DatabaseConnector()


def test_dialects():
    assert SQLiteConnector().dialect == "sqlite"
    assert PostgreSQLConnector().dialect == "postgresql"
    assert MySQLConnector().dialect == "mysql"
    assert SQLServerConnector().dialect == "sqlserver"


def test_sqlite_crud_roundtrip():
    async def run():
        db = SQLiteConnector(":memory:")
        assert not db.is_connected
        await db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        row_id = await db.execute("INSERT INTO users (name) VALUES (?)", ("ada",))
        assert row_id == 1
        one = await db.fetch_one("SELECT * FROM users WHERE id = ?", (1,))
        assert one == {"id": 1, "name": "ada"}
        assert await db.fetch_one("SELECT * FROM users WHERE id = ?", (99,)) is None
        await db.execute("INSERT INTO users (name) VALUES (?)", ("grace",))
        all_rows = await db.fetch_all("SELECT * FROM users ORDER BY id")
        assert all_rows == [{"id": 1, "name": "ada"}, {"id": 2, "name": "grace"}]
        assert db.is_connected
        await db.disconnect()
        assert not db.is_connected

    asyncio.run(run())


def test_sqlite_context_manager():
    async def run():
        async with SQLiteConnector(":memory:") as db:
            assert db.is_connected
            await db.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        assert not db.is_connected

    asyncio.run(run())


def _force_import_error(monkeypatch, name):
    monkeypatch.setitem(sys.modules, name, None)


def test_missing_driver_errors_are_actionable(monkeypatch):
    _force_import_error(monkeypatch, "asyncpg")
    _force_import_error(monkeypatch, "aiomysql")
    _force_import_error(monkeypatch, "aioodbc")
    for connector in (
        PostgreSQLConnector(database="x"),
        MySQLConnector(database="x"),
        SQLServerConnector(database="x"),
    ):
        with pytest.raises(RuntimeError, match="pip install meraki\\["):
            asyncio.run(connector.connect())
