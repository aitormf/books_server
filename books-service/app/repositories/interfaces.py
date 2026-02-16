from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities import Author, Book


class IBookRepository(ABC):
    """Abstract interface for the book repository.

    Defines the contract that any persistence implementation
    (PostgreSQL, MongoDB, etc.) must fulfill.
    """

    @abstractmethod
    async def create(self, book: Book) -> Book:
        """Create a new book."""

    @abstractmethod
    async def get_by_id(self, book_id: int) -> Optional[Book]:
        """Get a book by ID."""

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """List books with pagination."""

    @abstractmethod
    async def update(self, book_id: int, book: Book) -> Optional[Book]:
        """Update an existing book."""

    @abstractmethod
    async def delete(self, book_id: int) -> bool:
        """Delete a book."""

    @abstractmethod
    async def add_authors(self, book_id: int, author_ids: List[int]) -> bool:
        """Add authors to a book."""

    @abstractmethod
    async def remove_author(self, book_id: int, author_id: int) -> bool:
        """Remove an author from a book."""

    @abstractmethod
    async def get_authors_by_book(self, book_id: int) -> List[Author]:
        """Get authors assigned to a book."""


class IAuthorsCache(ABC):
    """Abstract interface for the authors cache."""

    @abstractmethod
    async def save_author(
        self, author_id: int, name: str, nationality: Optional[str]
    ) -> None:
        """Save or update an author in the cache."""

    @abstractmethod
    async def get_author(self, author_id: int) -> Optional[Author]:
        """Get an author from the cache."""

    @abstractmethod
    async def delete_author(self, author_id: int) -> None:
        """Delete an author from the cache."""
