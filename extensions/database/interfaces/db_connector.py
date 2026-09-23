from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple


class DatabaseConnector(ABC):
    """Abstract base class defining the database interface."""

    @abstractmethod
    def connect(self) -> None:
        """connection to the database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the database."""
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> None:
        """Execute a write/mutation query (INSERT, UPDATE, DELETE operations here)."""
        pass

    @abstractmethod
    def fetch_one(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[dict[str, Any]]:
        """Fetch a single record matching the query."""
        pass

    @abstractmethod
    def fetch_all(
        self, query: str, params: Optional[Tuple[Any, ...]] = None
    ) -> list[dict[str, Any]]:
        """Fetch all records matching the query."""
        pass