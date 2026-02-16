from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.entities import Author, Book


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    publication_year: Optional[int] = None


class BookUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    publication_year: Optional[int] = None


class AuthorResponse(BaseModel):
    id: int
    name: str
    nationality: Optional[str] = None

    @classmethod
    def from_entity(cls, entity: Author) -> "AuthorResponse":
        return cls(
            id=entity.id,
            name=entity.name,
            nationality=entity.nationality,
        )


class BookResponse(BaseModel):
    id: int
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    authors: List[AuthorResponse] = []

    @classmethod
    def from_entity(cls, entity: Book) -> "BookResponse":
        authors = (
            [AuthorResponse.from_entity(a) for a in entity.authors]
            if entity.authors
            else []
        )
        return cls(
            id=entity.id,
            title=entity.title,
            isbn=entity.isbn,
            publication_year=entity.publication_year,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            authors=authors,
        )


class AssignAuthorsRequest(BaseModel):
    author_ids: List[int] = Field(..., min_length=1)


class ErrorResponse(BaseModel):
    error: str
    message: str
    correlation_id: Optional[str] = None
