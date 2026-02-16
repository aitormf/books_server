from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import List, Optional

from app.domain.entities import Author, Book

EventHandler = Callable[[dict], Awaitable[None]]


class IAuthorRepository(ABC):
    """Abstract interface for the author repository.

    Defines the contract that any persistence implementation
    (PostgreSQL, MongoDB, etc.) must fulfill.
    """

    @abstractmethod
    async def create(self, author: Author) -> Author:
        """Create a new author."""

    @abstractmethod
    async def get_by_id(self, author_id: int) -> Optional[Author]:
        """Get an author by ID."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Author]:
        """List authors with pagination."""

    @abstractmethod
    async def update(self, author_id: int, author: Author) -> Optional[Author]:
        """Update an existing author."""

    @abstractmethod
    async def delete(self, author_id: int) -> bool:
        """Delete an author."""

    @abstractmethod
    async def add_books(self, author_id: int, book_ids: List[int]) -> bool:
        """Add books to an author."""

    @abstractmethod
    async def remove_book(self, author_id: int, book_id: int) -> bool:
        """Remove a book from an author."""

    @abstractmethod
    async def get_books_by_author(self, author_id: int) -> List[Book]:
        """Get books assigned to an author."""

    @abstractmethod
    async def remove_book_from_all_authors(self, book_id: int) -> None:
        """Remove all author-book links for a given book."""


class IBooksCache(ABC):
    """Abstract interface for the books cache."""

    @abstractmethod
    async def save_book(
        self, book_id: int, title: str, isbn: Optional[str], year: Optional[int]
    ) -> None:
        """Save or update a book in the cache."""

    @abstractmethod
    async def get_book(self, book_id: int) -> Optional[Book]:
        """Get a book from the cache."""

    @abstractmethod
    async def delete_book(self, book_id: int) -> None:
        """Delete a book from the cache."""


class IEventPublisher(ABC):
    """Abstract interface for publishing domain events."""

    @abstractmethod
    async def start(self) -> None:
        """Start the publisher connection."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the publisher connection."""

    @abstractmethod
    async def publish(
        self, topic: str, data: dict, correlation_id: str | None = None
    ) -> None:
        """Publish an event to the given topic."""


class IEventConsumer(ABC):
    """Abstract interface for consuming domain events."""

    @abstractmethod
    async def start(self) -> None:
        """Start the consumer loop."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the consumer."""

    @abstractmethod
    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
