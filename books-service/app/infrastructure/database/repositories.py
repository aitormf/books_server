from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Author, Book
from app.infrastructure.database.models import AuthorsCacheModel, BookAuthorModel, BookModel
from app.repositories.interfaces import IAuthorsCache, IBookRepository


class PostgreSQLBookRepository(IBookRepository):
    """PostgreSQL + SQLAlchemy implementation of the book repository.

    This class knows about SQLAlchemy, but the rest of the application does not.
    To switch to MongoDB, only this class needs to change.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, book: Book) -> Book:
        db_book = BookModel(
            title=book.title,
            isbn=book.isbn,
            publication_year=book.publication_year,
        )
        self.session.add(db_book)
        await self.session.commit()
        await self.session.refresh(db_book)
        return self._to_entity(db_book)

    async def get_by_id(self, book_id: int) -> Optional[Book]:
        db_book = await self.session.get(BookModel, book_id)
        if not db_book:
            return None
        return self._to_entity(db_book)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Book]:
        stmt = select(BookModel).offset(skip).limit(limit).order_by(BookModel.id)
        result = await self.session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def update(self, book_id: int, book: Book) -> Optional[Book]:
        db_book = await self.session.get(BookModel, book_id)
        if not db_book:
            return None
        db_book.title = book.title
        db_book.isbn = book.isbn
        db_book.publication_year = book.publication_year
        await self.session.commit()
        await self.session.refresh(db_book)
        return self._to_entity(db_book)

    async def delete(self, book_id: int) -> bool:
        db_book = await self.session.get(BookModel, book_id)
        if not db_book:
            return False
        await self.session.delete(db_book)
        await self.session.commit()
        return True

    async def add_authors(self, book_id: int, author_ids: List[int]) -> bool:
        for author_id in author_ids:
            stmt = pg_insert(BookAuthorModel).values(
                book_id=book_id, author_id=author_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def remove_author(self, book_id: int, author_id: int) -> bool:
        stmt = delete(BookAuthorModel).where(
            BookAuthorModel.book_id == book_id,
            BookAuthorModel.author_id == author_id,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def remove_author_from_all_books(self, author_id: int) -> None:
        await self.session.execute(
            delete(BookAuthorModel).where(BookAuthorModel.author_id == author_id)
        )
        await self.session.commit()

    async def get_authors_by_book(self, book_id: int) -> List[Author]:
        stmt = (
            select(AuthorsCacheModel)
            .join(BookAuthorModel, BookAuthorModel.author_id == AuthorsCacheModel.author_id)
            .where(BookAuthorModel.book_id == book_id)
        )
        result = await self.session.execute(stmt)
        return [self._author_to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, db_book: BookModel) -> Book:
        return Book(
            id=db_book.id,
            title=db_book.title,
            isbn=db_book.isbn,
            publication_year=db_book.publication_year,
            created_at=db_book.created_at,
            updated_at=db_book.updated_at,
        )

    def _author_to_entity(self, db_author: AuthorsCacheModel) -> Author:
        return Author(
            id=db_author.author_id,
            name=db_author.name,
            nationality=db_author.nationality,
        )


class PostgreSQLAuthorsCache(IAuthorsCache):
    """PostgreSQL implementation of the authors cache."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_author(
        self, author_id: int, name: str, nationality: Optional[str]
    ) -> None:
        stmt = pg_insert(AuthorsCacheModel).values(
            author_id=author_id,
            name=name,
            nationality=nationality,
        ).on_conflict_do_update(
            index_elements=["author_id"],
            set_={
                "name": name,
                "nationality": nationality,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_author(self, author_id: int) -> Optional[Author]:
        stmt = select(AuthorsCacheModel).where(
            AuthorsCacheModel.author_id == author_id
        )
        result = await self.session.execute(stmt)
        db_author = result.scalar_one_or_none()
        if not db_author:
            return None
        return Author(
            id=db_author.author_id,
            name=db_author.name,
            nationality=db_author.nationality,
        )

    async def delete_author(self, author_id: int) -> None:
        await self.session.execute(
            delete(AuthorsCacheModel).where(
                AuthorsCacheModel.author_id == author_id
            )
        )
        await self.session.commit()
