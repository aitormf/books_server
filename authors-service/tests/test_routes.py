from datetime import date, datetime

import pytest

from app.domain.entities import Author, Book


@pytest.mark.asyncio
async def test_create_author(client, author_service, sample_author_data):
    author_service.create_author.return_value = Author(
        id=1,
        name="Gabriel Garcia Marquez",
        birth_date=date(1927, 3, 6),
        nationality="Colombian",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )
    # Reset mock to clear any previous setup calls
    author_service.create_author.reset_mock()
    author_service.create_author.return_value = Author(
        id=1,
        name="Gabriel Garcia Marquez",
        birth_date=date(1927, 3, 6),
        nationality="Colombian",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )

    response = await client.post("/authors/", json=sample_author_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Gabriel Garcia Marquez"
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_author_validation_error(client, author_service):
    author_service.create_author.side_effect = ValueError("Author name must be at least 2 chars")

    response = await client.post("/authors/", json={
        "name": "A",
        "birth_date": "1990-01-01",
        "nationality": "ES",
    })

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_authors(client, author_service):
    author_service.get_all_authors.return_value = [
        Author(id=1, name="Author 1", birth_date=date(1990, 1, 1), nationality="ES"),
        Author(id=2, name="Author 2", birth_date=date(1985, 5, 10), nationality="FR"),
    ]

    response = await client.get("/authors/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Author 1"


@pytest.mark.asyncio
async def test_get_author(client, author_service):
    author = Author(
        id=1,
        name="Test Author",
        birth_date=date(1990, 1, 1),
        nationality="ES",
        books=[Book(id=10, title="Test Book", isbn="123-456", publication_year=2020)],
    )
    author_service.get_author_with_books.return_value = author

    response = await client.get("/authors/1")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Author"
    assert len(data["books"]) == 1
    assert data["books"][0]["title"] == "Test Book"


@pytest.mark.asyncio
async def test_get_author_not_found(client, author_service):
    author_service.get_author_with_books.return_value = None

    response = await client.get("/authors/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_author(client, author_service):
    updated = Author(
        id=1,
        name="Updated Name",
        birth_date=date(1990, 1, 1),
        nationality="FR",
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 2),
    )
    author_service.update_author.return_value = updated

    response = await client.put("/authors/1", json={
        "name": "Updated Name",
        "birth_date": "1990-01-01",
        "nationality": "FR",
    })

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_author_not_found(client, author_service):
    author_service.update_author.return_value = None

    response = await client.put("/authors/999", json={
        "name": "Updated Name",
        "birth_date": "1990-01-01",
        "nationality": "FR",
    })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_author(client, author_service):
    author_service.delete_author.return_value = True

    response = await client.delete("/authors/1")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_author_not_found(client, author_service):
    author_service.delete_author.return_value = False

    response = await client.delete("/authors/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_books(client, author_service):
    author_service.assign_books_to_author.return_value = True

    response = await client.post("/authors/1/books", json={"book_ids": [10, 20]})

    assert response.status_code == 200
    assert response.json()["message"] == "Books assigned successfully"


@pytest.mark.asyncio
async def test_assign_books_author_not_found(client, author_service):
    author_service.assign_books_to_author.side_effect = ValueError(
        "Author with id 999 not found"
    )

    response = await client.post("/authors/999/books", json={"book_ids": [1]})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unassign_book(client, author_service):
    author_service.unassign_book_from_author.return_value = True

    response = await client.delete("/authors/1/books/10")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_author_future_birth_date(client, author_service):
    response = await client.post("/authors/", json={
        "name": "Future Author",
        "birth_date": "2099-01-01",
        "nationality": "ES",
    })

    assert response.status_code == 422
