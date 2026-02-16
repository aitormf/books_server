from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services import AuthorService
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.repositories import (
    PostgreSQLAuthorRepository,
    PostgreSQLBooksCache,
)
from app.infrastructure.kafka.producer import kafka_producer


async def get_author_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthorService:
    """Factory for the AuthorService.

    This is where interfaces are connected to implementations.
    To switch to MongoDB, only this function needs to change.
    """
    author_repo = PostgreSQLAuthorRepository(session)
    books_cache = PostgreSQLBooksCache(session)
    return AuthorService(
        author_repo=author_repo,
        books_cache=books_cache,
        event_publisher=kafka_producer,
    )
