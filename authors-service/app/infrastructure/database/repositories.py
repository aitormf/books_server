from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Author, Book
from app.infrastructure.database.models import AuthorBookModel, AuthorModel, BooksCacheModel
from app.repositories.interfaces import IAuthorRepository, IBooksCache


class PostgreSQLAuthorRepository(IAuthorRepository):
    """PostgreSQL + SQLAlchemy implementation of the author repository.

    This class knows about SQLAlchemy, but the rest of the application does not.
    To switch to MongoDB, only this class needs to change.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, author: Author) -> Author:
        db_author = AuthorModel(
            name=author.name,
            birth_date=author.birth_date,
            nationality=author.nationality,
        )
        self.session.add(db_author)
        await self.session.commit()
        await self.session.refresh(db_author)
        return self._to_entity(db_author)

    async def get_by_id(self, author_id: int) -> Optional[Author]:
        db_author = await self.session.get(AuthorModel, author_id)
        if not db_author:
            return None
        return self._to_entity(db_author)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Author]:
        stmt = select(AuthorModel).offset(skip).limit(limit).order_by(AuthorModel.id)
        result = await self.session.execute(stmt)
        return [self._to_entity(row) for row in result.scalars().all()]

    async def update(self, author_id: int, author: Author) -> Optional[Author]:
        db_author = await self.session.get(AuthorModel, author_id)
        if not db_author:
            return None
        db_author.name = author.name
        db_author.birth_date = author.birth_date
        db_author.nationality = author.nationality
        await self.session.commit()
        await self.session.refresh(db_author)
        return self._to_entity(db_author)

    async def delete(self, author_id: int) -> bool:
        db_author = await self.session.get(AuthorModel, author_id)
        if not db_author:
            return False
        await self.session.delete(db_author)
        await self.session.commit()
        return True

    async def add_books(self, author_id: int, book_ids: List[int]) -> bool:
        for book_id in book_ids:
            stmt = pg_insert(AuthorBookModel).values(
                author_id=author_id, book_id=book_id
            ).on_conflict_do_nothing()
            await self.session.execute(stmt)
        await self.session.commit()
        return True

    async def remove_book(self, author_id: int, book_id: int) -> bool:
        stmt = delete(AuthorBookModel).where(
            AuthorBookModel.author_id == author_id,
            AuthorBookModel.book_id == book_id,
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def get_books_by_author(self, author_id: int) -> List[Book]:
        stmt = (
            select(BooksCacheModel)
            .join(AuthorBookModel, AuthorBookModel.book_id == BooksCacheModel.book_id)
            .where(AuthorBookModel.author_id == author_id)
        )
        result = await self.session.execute(stmt)
        return [self._book_to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, db_author: AuthorModel) -> Author:
        return Author(
            id=db_author.id,
            name=db_author.name,
            birth_date=db_author.birth_date,
            nationality=db_author.nationality,
            created_at=db_author.created_at,
            updated_at=db_author.updated_at,
        )

    def _book_to_entity(self, db_book: BooksCacheModel) -> Book:
        return Book(
            id=db_book.book_id,
            title=db_book.title,
            isbn=db_book.isbn,
            publication_year=db_book.publication_year,
        )


class PostgreSQLBooksCache(IBooksCache):
    """PostgreSQL implementation of the books cache."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_book(
        self, book_id: int, title: str, isbn: Optional[str], year: Optional[int]
    ) -> None:
        stmt = pg_insert(BooksCacheModel).values(
            book_id=book_id,
            title=title,
            isbn=isbn,
            publication_year=year,
        ).on_conflict_do_update(
            index_elements=["book_id"],
            set_={
                "title": title,
                "isbn": isbn,
                "publication_year": year,
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_book(self, book_id: int) -> Optional[Book]:
        stmt = select(BooksCacheModel).where(BooksCacheModel.book_id == book_id)
        result = await self.session.execute(stmt)
        db_book = result.scalar_one_or_none()
        if not db_book:
            return None
        return Book(
            id=db_book.book_id,
            title=db_book.title,
            isbn=db_book.isbn,
            publication_year=db_book.publication_year,
        )

    async def delete_book(self, book_id: int) -> None:
        await self.session.execute(
            delete(BooksCacheModel).where(BooksCacheModel.book_id == book_id)
        )
        await self.session.commit()
