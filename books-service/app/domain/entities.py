from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Author:
    """Domain entity for an Author (cached from Authors Service)."""

    id: Optional[int]
    name: str
    nationality: Optional[str] = None


@dataclass
class Book:
    """Domain entity for a Book.

    Pure Python class with no ORM dependencies.
    Represents the business concept of a book.
    """

    id: Optional[int]
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    authors: List[Author] = field(default_factory=list)
