import pytest
import pytest_asyncio
from meraki_db.implementations.sqlite import SQLiteConnector
from meraki_db.interfaces.connector import DatabaseConnector


@pytest_asyncio.fixture
async def connector():
    conn = SQLiteConnector(database=":memory:")
    await conn.connect()
    await conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    yield conn
    await conn.disconnect()


@pytest.mark.asyncio
async def test_satisfies_contract():
    conn = SQLiteConnector()
    assert isinstance(conn, DatabaseConnector)


@pytest.mark.asyncio
async def test_connect_and_disconnect():
    conn = SQLiteConnector(database=":memory:")
    await conn.connect()
    assert conn._connection is not None

    await conn.disconnect()
    assert conn._connection is None


@pytest.mark.asyncio
async def test_execute_and_fetch_one(connector):
    await connector.execute(
        "INSERT INTO users (id, name) VALUES (?, ?);", 
        (1, "Alice")
    )

    result = await connector.fetch_one("SELECT * FROM users WHERE id = ?;", (1,))
    assert result is not None
    assert result["id"] == 1
    assert result["name"] == "Alice"

    result_none = await connector.fetch_one("SELECT * FROM users WHERE id = ?;", (999,))
    assert result_none is None


@pytest.mark.asyncio
async def test_fetch_all(connector):
    await connector.execute("INSERT INTO users (id, name) VALUES (?, ?);", (1, "Alice"))
    await connector.execute("INSERT INTO users (id, name) VALUES (?, ?);", (2, "Bob"))

    results = await connector.fetch_all("SELECT * FROM users ORDER BY id ASC;")
    assert len(results) == 2
    assert results[0]["name"] == "Alice"
    assert results[1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_uninitialized_connection():
    conn = SQLiteConnector()
    with pytest.raises(RuntimeError, match="Database is not connected. Call connect\\(\\) first."):
        await conn.execute("SELECT 1;")