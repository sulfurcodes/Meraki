import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from meraki_db.implementations.postgresql import PostgreSQLConnector
from meraki_db.interfaces.connector import DatabaseConnector


@pytest.fixture
def mock_pool():
    pool = MagicMock()
    conn = AsyncMock()
    # Properly mock the async context manager returned by pool.acquire()
    ctx_manager = MagicMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=conn)
    ctx_manager.__aexit__ = AsyncMock(return_value=None)
    pool.acquire.return_value = ctx_manager
    return pool, conn


@pytest.mark.asyncio
async def test_satisfies_contract():
    connector = PostgreSQLConnector()
    assert isinstance(connector, DatabaseConnector)


@pytest.mark.asyncio
async def test_connect_disconnect():
    connector = PostgreSQLConnector(dsn="postgres://user:pass@localhost/db")
    with patch('meraki_db.implementations.postgresql.asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
        pool_mock = AsyncMock()
        mock_create_pool.return_value = pool_mock

        await connector.connect()
        mock_create_pool.assert_awaited_once_with(dsn="postgres://user:pass@localhost/db")
        assert connector.pool == pool_mock

        await connector.disconnect()
        pool_mock.close.assert_awaited_once()
        assert connector.pool is None


@pytest.mark.asyncio
async def test_connect_with_params():
    connector = PostgreSQLConnector(host="db", port=5432, user="u", password="p", database="d")
    with patch('meraki_db.implementations.postgresql.asyncpg.create_pool', new_callable=AsyncMock) as mock_create_pool:
        await connector.connect()
        mock_create_pool.assert_awaited_once_with(
            host="db", port=5432, user="u", password="p", database="d"
        )


@pytest.mark.asyncio
async def test_execute(mock_pool):
    pool, conn = mock_pool
    connector = PostgreSQLConnector()
    connector.pool = pool

    await connector.execute("INSERT INTO users (name) VALUES (:name)", {"name": "Alice"})
    conn.execute.assert_awaited_once_with("INSERT INTO users (name) VALUES ($1)", "Alice")


@pytest.mark.asyncio
async def test_fetch_one(mock_pool):
    pool, conn = mock_pool
    connector = PostgreSQLConnector()
    connector.pool = pool

    conn.fetchrow.return_value = {"id": 1, "name": "Alice"}

    result = await connector.fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
    conn.fetchrow.assert_awaited_once_with("SELECT * FROM users WHERE id = $1", 1)
    assert result == {"id": 1, "name": "Alice"}

    # Test returning None
    conn.fetchrow.return_value = None
    result_none = await connector.fetch_one("SELECT * FROM nothing")
    assert result_none is None


@pytest.mark.asyncio
async def test_fetch_all(mock_pool):
    pool, conn = mock_pool
    connector = PostgreSQLConnector()
    connector.pool = pool

    conn.fetch.return_value = [{"id": 1, "name": "Alice"}]

    result = await connector.fetch_all("SELECT * FROM users")
    conn.fetch.assert_awaited_once_with("SELECT * FROM users")
    assert result == [{"id": 1, "name": "Alice"}]


@pytest.mark.asyncio
async def test_uninitialized_pool():
    connector = PostgreSQLConnector()
    with pytest.raises(RuntimeError, match="Database connection pool is not initialized"):
        await connector.execute("SELECT 1")
