from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional


class DatabaseConnector(ABC):
    """
    Generic DatabaseConnector interface using the Strategy Pattern.
    Concrete implementations (e.g. PostgreSQL, MySQL) must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the database."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    async def execute(self, query: str, params=None):
        """Execute a query (insert, update, delete)."""
        pass

    @abstractmethod
    async def fetch_one(self, query: str, params=None):
        """Fetch a single record from the database."""
        pass

    @abstractmethod
    async def fetch_all(self, query: str, params=None):
        """Fetch multiple records from the database."""
        pass