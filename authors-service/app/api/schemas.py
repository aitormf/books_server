from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.entities import Author, Book


class AuthorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    birth_date: date
    nationality: str = Field(..., max_length=100)

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class AuthorUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    birth_date: date
    nationality: str = Field(..., max_length=100)

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Birth date cannot be in the future")
        return v


class BookResponse(BaseModel):
    id: int
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None

    @classmethod
    def from_entity(cls, entity: Book) -> "BookResponse":
        return cls(
            id=entity.id,
            title=entity.title,
            isbn=entity.isbn,
            publication_year=entity.publication_year,
        )


class AuthorResponse(BaseModel):
    id: int
    name: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    books: List[BookResponse] = []

    @classmethod
    def from_entity(cls, entity: Author) -> "AuthorResponse":
        books = [BookResponse.from_entity(b) for b in entity.books] if entity.books else []
        return cls(
            id=entity.id,
            name=entity.name,
            birth_date=entity.birth_date,
            nationality=entity.nationality,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            books=books,
        )


class AssignBooksRequest(BaseModel):
    book_ids: List[int] = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    error: str
    message: str
    correlation_id: Optional[str] = None
