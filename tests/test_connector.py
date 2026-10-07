import pytest
from typing import Optional, Dict, Any, List
from meraki_db.interfaces.connector import DatabaseConnector


def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError, match="Can't instantiate abstract class DatabaseConnector"):
        DatabaseConnector()


def test_can_instantiate_concrete_class():
    class DummyConnector(DatabaseConnector):
        async def connect(self) -> None:
            pass

        async def disconnect(self) -> None:
            pass

        async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
            return None

        async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
            return None

        async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            return []

    connector = DummyConnector()
    assert isinstance(connector, DatabaseConnector)
