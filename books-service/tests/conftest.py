from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_book_service
from app.domain.entities import Book
from app.domain.services import BookService
from app.main import app


@pytest.fixture
def book_service():
    return AsyncMock(spec=BookService)


@pytest.fixture
async def client(book_service):
    async def override():
        return book_service

    app.dependency_overrides[get_book_service] = override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_book():
    return Book(
        id=1,
        title="Cien anos de soledad",
        isbn="978-0060883287",
        publication_year=1967,
    )


@pytest.fixture
def sample_book_data():
    return {
        "title": "Cien anos de soledad",
        "isbn": "978-0060883287",
        "publication_year": 1967,
    }
