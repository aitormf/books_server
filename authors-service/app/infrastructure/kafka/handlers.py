from collections.abc import AsyncIterator, Callable

from app.domain.services import AuthorService
from app.repositories.interfaces import EventHandler


def create_book_event_handlers(
    service_factory: Callable[[], AsyncIterator[AuthorService]],
) -> dict[str, EventHandler]:
    """Create event handlers that delegate to the domain service.

    ``service_factory`` is an async context manager that yields an
    ``AuthorService`` with ``event_publisher=None`` so that processing
    an incoming event never triggers outgoing events (no cascades).
    """

    async def handle_book_created_or_updated(data: dict) -> None:
        """Upsert book into local cache (idempotent)."""
        async with service_factory() as service:
            await service.sync_book_to_cache(
                book_id=data["book_id"],
                title=data["title"],
                isbn=data.get("isbn"),
                year=data.get("publication_year"),
            )

    async def handle_book_deleted(data: dict) -> None:
        """Remove book from cache and all relationships."""
        async with service_factory() as service:
            await service.remove_book_from_cache_and_authors(data["book_id"])

    async def handle_book_author_linked(data: dict) -> None:
        """Sync relationship created by the books service."""
        async with service_factory() as service:
            await service.sync_book_linked(data["author_id"], data["book_id"])

    async def handle_book_author_unlinked(data: dict) -> None:
        """Sync relationship removal from the books service."""
        async with service_factory() as service:
            await service.sync_book_unlinked(data["author_id"], data["book_id"])

    return {
        "book.created": handle_book_created_or_updated,
        "book.updated": handle_book_created_or_updated,
        "book.deleted": handle_book_deleted,
        "book_author.linked": handle_book_author_linked,
        "book_author.unlinked": handle_book_author_unlinked,
    }
