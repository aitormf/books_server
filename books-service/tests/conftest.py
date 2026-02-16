from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_book_service
from app.domain.entities import Book
from app.domain.services import BookService
from app.main import app


@pytest.fixture
def mock_book_repo():
    return AsyncMock()


@pytest.fixture
def mock_authors_cache():
    return AsyncMock()


@pytest.fixture
def mock_event_publisher():
    return AsyncMock()


@pytest.fixture
def book_service(mock_book_repo, mock_authors_cache, mock_event_publisher):
    return BookService(
        book_repo=mock_book_repo,
        authors_cache=mock_authors_cache,
        event_publisher=mock_event_publisher,
    )


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
