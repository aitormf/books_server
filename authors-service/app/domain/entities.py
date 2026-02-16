from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List


@dataclass
class Book:
    """Domain entity for a Book (cached from Books Service)."""

    id: Optional[int]
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Author:
    """Domain entity for an Author.

    Pure Python class with no ORM dependencies.
    Represents the business concept of an author.
    """

    id: Optional[int]
    name: str
    birth_date: Optional[date] = None
    nationality: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    books: List[Book] = field(default_factory=list)
