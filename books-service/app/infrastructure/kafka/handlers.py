from collections.abc import AsyncIterator, Callable

from app.domain.services import BookService
from app.repositories.interfaces import EventHandler


def create_author_event_handlers(
    service_factory: Callable[[], AsyncIterator[BookService]],
) -> dict[str, EventHandler]:
    """Create event handlers that delegate to the domain service.

    ``service_factory`` is an async context manager that yields a
    ``BookService`` with ``event_publisher=None`` so that processing
    an incoming event never triggers outgoing events (no cascades).
    """

    async def handle_author_created_or_updated(data: dict) -> None:
        """Upsert author into local cache (idempotent)."""
        async with service_factory() as service:
            await service.sync_author_to_cache(
                author_id=data["author_id"],
                name=data["name"],
                nationality=data.get("nationality"),
            )

    async def handle_author_deleted(data: dict) -> None:
        """Remove author from cache and all relationships."""
        async with service_factory() as service:
            await service.remove_author_from_cache_and_books(data["author_id"])

    async def handle_author_book_linked(data: dict) -> None:
        """Sync relationship created by the authors service."""
        async with service_factory() as service:
            await service.sync_author_linked(data["book_id"], data["author_id"])

    async def handle_author_book_unlinked(data: dict) -> None:
        """Sync relationship removal from the authors service."""
        async with service_factory() as service:
            await service.sync_author_unlinked(data["book_id"], data["author_id"])

    return {
        "author.created": handle_author_created_or_updated,
        "author.updated": handle_author_created_or_updated,
        "author.deleted": handle_author_deleted,
        "author_book.linked": handle_author_book_linked,
        "author_book.unlinked": handle_author_book_unlinked,
    }
