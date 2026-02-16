from typing import List, Optional

from app.domain.entities import Book
from app.repositories.interfaces import IAuthorsCache, IBookRepository


class BookService:
    """Domain service containing business logic.

    Does NOT know implementation details (PostgreSQL, MongoDB, etc.).
    Only works with abstract interfaces.
    """

    def __init__(
        self,
        book_repo: IBookRepository,
        authors_cache: IAuthorsCache,
        event_publisher: object | None = None,
    ) -> None:
        self.book_repo = book_repo
        self.authors_cache = authors_cache
        self.event_publisher = event_publisher

    async def _publish(
        self, topic: str, data: dict, correlation_id: str | None = None
    ) -> None:
        if self.event_publisher:
            await self.event_publisher.publish(topic, data, correlation_id)

    async def create_book(
        self, book: Book, correlation_id: str | None = None
    ) -> Book:
        """Create a book with business validations."""
        if not book.title or len(book.title.strip()) < 1:
            raise ValueError("Book title must not be empty")

        created = await self.book_repo.create(book)
        await self._publish(
            "book.created",
            {
                "book_id": created.id,
                "title": created.title,
                "isbn": created.isbn,
                "publication_year": created.publication_year,
            },
            correlation_id,
        )
        return created

    async def get_book_with_authors(self, book_id: int) -> Optional[Book]:
        """Get a book with its assigned authors."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return None
        authors = await self.book_repo.get_authors_by_book(book_id)
        book.authors = authors
        return book

    async def get_all_books(self, skip: int = 0, limit: int = 100) -> List[Book]:
        """List all books with pagination."""
        return await self.book_repo.get_all(skip=skip, limit=limit)

    async def update_book(
        self, book_id: int, book: Book, correlation_id: str | None = None
    ) -> Optional[Book]:
        """Update an existing book."""
        if not book.title or len(book.title.strip()) < 1:
            raise ValueError("Book title must not be empty")

        updated = await self.book_repo.update(book_id, book)
        if updated:
            await self._publish(
                "book.updated",
                {
                    "book_id": updated.id,
                    "title": updated.title,
                    "isbn": updated.isbn,
                    "publication_year": updated.publication_year,
                },
                correlation_id,
            )
        return updated

    async def delete_book(
        self, book_id: int, correlation_id: str | None = None
    ) -> bool:
        """Delete a book and publish event."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            return False
        deleted = await self.book_repo.delete(book_id)
        if deleted:
            await self._publish(
                "book.deleted",
                {"book_id": book_id},
                correlation_id,
            )
        return deleted

    async def assign_authors_to_book(
        self,
        book_id: int,
        author_ids: List[int],
        correlation_id: str | None = None,
    ) -> bool:
        """Assign authors to a book with validations."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        for author_id in author_ids:
            author = await self.authors_cache.get_author(author_id)
            if not author:
                raise ValueError(f"Author with id {author_id} not found in cache")

        result = await self.book_repo.add_authors(book_id, author_ids)

        for author_id in author_ids:
            await self._publish(
                "book_author.linked",
                {"book_id": book_id, "author_id": author_id},
                correlation_id,
            )
        return result

    async def unassign_author_from_book(
        self,
        book_id: int,
        author_id: int,
        correlation_id: str | None = None,
    ) -> bool:
        """Remove an author from a book."""
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        result = await self.book_repo.remove_author(book_id, author_id)
        if result:
            await self._publish(
                "book_author.unlinked",
                {"book_id": book_id, "author_id": author_id},
                correlation_id,
            )
        return result
