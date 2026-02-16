from typing import List, Optional

from app.domain.entities import Author
from app.repositories.interfaces import IAuthorRepository, IBooksCache, IEventPublisher


class AuthorService:
    """Domain service containing business logic.

    Does NOT know implementation details (PostgreSQL, MongoDB, etc.).
    Only works with abstract interfaces.
    """

    def __init__(
        self,
        author_repo: IAuthorRepository,
        books_cache: IBooksCache,
        event_publisher: IEventPublisher | None = None,
        commit=None,
    ) -> None:
        self.author_repo = author_repo
        self.books_cache = books_cache
        self.event_publisher = event_publisher
        self._commit = commit or self._noop

    @staticmethod
    async def _noop():
        pass

    async def _publish(
        self, topic: str, data: dict, correlation_id: str | None = None
    ) -> None:
        if self.event_publisher:
            await self.event_publisher.publish(topic, data, correlation_id)

    async def create_author(
        self, author: Author, correlation_id: str | None = None
    ) -> Author:
        """Create an author with business validations."""
        if not author.name or len(author.name.strip()) < 2:
            raise ValueError("Author name must be at least 2 characters")

        created = await self.author_repo.create(author)
        await self._commit()
        await self._publish(
            "author.created",
            {
                "author_id": created.id,
                "name": created.name,
                "birth_date": str(created.birth_date) if created.birth_date else None,
                "nationality": created.nationality,
            },
            correlation_id,
        )
        return created

    async def get_author_with_books(self, author_id: int) -> Optional[Author]:
        """Get an author with their assigned books."""
        author = await self.author_repo.get_by_id(author_id)
        if not author:
            return None
        books = await self.author_repo.get_books_by_author(author_id)
        author.books = books
        return author

    async def get_all_authors(self, skip: int = 0, limit: int = 100) -> List[Author]:
        """List all authors with pagination."""
        return await self.author_repo.get_all(skip=skip, limit=limit)

    async def update_author(
        self, author_id: int, author: Author, correlation_id: str | None = None
    ) -> Optional[Author]:
        """Update an existing author."""
        if not author.name or len(author.name.strip()) < 2:
            raise ValueError("Author name must be at least 2 characters")

        updated = await self.author_repo.update(author_id, author)
        if updated:
            await self._commit()
            await self._publish(
                "author.updated",
                {
                    "author_id": updated.id,
                    "name": updated.name,
                    "birth_date": str(updated.birth_date) if updated.birth_date else None,
                    "nationality": updated.nationality,
                },
                correlation_id,
            )
        return updated

    async def delete_author(
        self, author_id: int, correlation_id: str | None = None
    ) -> bool:
        """Delete an author and publish event."""
        author = await self.author_repo.get_by_id(author_id)
        if not author:
            return False
        deleted = await self.author_repo.delete(author_id)
        if deleted:
            await self._commit()
            await self._publish(
                "author.deleted",
                {"author_id": author_id},
                correlation_id,
            )
        return deleted

    async def assign_books_to_author(
        self,
        author_id: int,
        book_ids: List[int],
        correlation_id: str | None = None,
    ) -> bool:
        """Assign books to an author with validations."""
        author = await self.author_repo.get_by_id(author_id)
        if not author:
            raise ValueError(f"Author with id {author_id} not found")

        for book_id in book_ids:
            book = await self.books_cache.get_book(book_id)
            if not book:
                raise ValueError(f"Book with id {book_id} not found in cache")

        result = await self.author_repo.add_books(author_id, book_ids)
        await self._commit()

        for book_id in book_ids:
            await self._publish(
                "author_book.linked",
                {"author_id": author_id, "book_id": book_id},
                correlation_id,
            )
        return result

    async def unassign_book_from_author(
        self,
        author_id: int,
        book_id: int,
        correlation_id: str | None = None,
    ) -> bool:
        """Remove a book from an author."""
        author = await self.author_repo.get_by_id(author_id)
        if not author:
            raise ValueError(f"Author with id {author_id} not found")

        result = await self.author_repo.remove_book(author_id, book_id)
        if result:
            await self._commit()
            await self._publish(
                "author_book.unlinked",
                {"author_id": author_id, "book_id": book_id},
                correlation_id,
            )
        return result

    # ── Sync methods for Kafka event handlers (no events published) ──

    async def sync_book_to_cache(
        self, book_id: int, title: str, isbn: str | None, year: int | None
    ) -> None:
        """Upsert a book into the local cache (called from event handlers)."""
        await self.books_cache.save_book(book_id=book_id, title=title, isbn=isbn, year=year)
        await self._commit()

    async def remove_book_from_cache_and_authors(self, book_id: int) -> None:
        """Remove a book from all authors and from the cache."""
        await self.author_repo.remove_book_from_all_authors(book_id)
        await self.books_cache.delete_book(book_id)
        await self._commit()

    async def sync_book_linked(self, author_id: int, book_id: int) -> None:
        """Sync a book-author link created by the books service."""
        await self.author_repo.add_books(author_id, [book_id])
        await self._commit()

    async def sync_book_unlinked(self, author_id: int, book_id: int) -> None:
        """Sync a book-author unlink from the books service."""
        await self.author_repo.remove_book(author_id, book_id)
        await self._commit()
