from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services import BookService
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.repositories import (
    PostgreSQLAuthorsCache,
    PostgreSQLBookRepository,
)
from app.infrastructure.kafka.producer import kafka_producer


async def get_book_service(
    session: AsyncSession = Depends(get_db_session),
) -> BookService:
    """Factory for the BookService.

    This is where interfaces are connected to implementations.
    To switch to MongoDB, only this function needs to change.
    """
    book_repo = PostgreSQLBookRepository(session)
    authors_cache = PostgreSQLAuthorsCache(session)
    return BookService(
        book_repo=book_repo,
        authors_cache=authors_cache,
        event_publisher=kafka_producer,
    )
