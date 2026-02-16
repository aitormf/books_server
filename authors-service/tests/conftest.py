from datetime import date
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_author_service
from app.domain.entities import Author
from app.domain.services import AuthorService
from app.main import app


@pytest.fixture
def author_service():
    return AsyncMock(spec=AuthorService)


@pytest.fixture
async def client(author_service):
    async def override():
        return author_service

    app.dependency_overrides[get_author_service] = override
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_author():
    return Author(
        id=1,
        name="Gabriel Garcia Marquez",
        birth_date=date(1927, 3, 6),
        nationality="Colombian",
    )


@pytest.fixture
def sample_author_data():
    return {
        "name": "Gabriel Garcia Marquez",
        "birth_date": "1927-03-06",
        "nationality": "Colombian",
    }
