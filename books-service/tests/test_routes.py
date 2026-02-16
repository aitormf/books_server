from datetime import datetime

import pytest

from app.domain.entities import Author, Book


@pytest.mark.asyncio
async def test_create_book(client, book_service, sample_book_data):
    book_service.create_book.return_value = Book(
        id=1,
        title="Cien anos de soledad",
        isbn="978-0060883287",
        publication_year=1967,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 1),
    )

    response = await client.post("/books/", json=sample_book_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Cien anos de soledad"
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_create_book_validation_error(client, book_service):
    book_service.create_book.side_effect = ValueError("Book title must not be empty")

    response = await client.post("/books/", json={
        "title": "",
        "publication_year": 2020,
    })

    # Pydantic validation catches min_length=1 before reaching the service
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_books(client, book_service):
    book_service.get_all_books.return_value = [
        Book(id=1, title="Book 1", publication_year=2020),
        Book(id=2, title="Book 2", publication_year=2021),
    ]

    response = await client.get("/books/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Book 1"


@pytest.mark.asyncio
async def test_get_book(client, book_service):
    book = Book(
        id=1,
        title="Test Book",
        isbn="123-456",
        publication_year=2020,
        authors=[Author(id=1, name="Test Author", nationality="ES")],
    )
    book_service.get_book_with_authors.return_value = book

    response = await client.get("/books/1")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert len(data["authors"]) == 1
    assert data["authors"][0]["name"] == "Test Author"


@pytest.mark.asyncio
async def test_get_book_not_found(client, book_service):
    book_service.get_book_with_authors.return_value = None

    response = await client.get("/books/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_book(client, book_service):
    updated = Book(
        id=1,
        title="Updated Title",
        isbn="999",
        publication_year=2025,
        created_at=datetime(2025, 1, 1),
        updated_at=datetime(2025, 1, 2),
    )
    book_service.update_book.return_value = updated

    response = await client.put("/books/1", json={
        "title": "Updated Title",
        "isbn": "999",
        "publication_year": 2025,
    })

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_book_not_found(client, book_service):
    book_service.update_book.return_value = None

    response = await client.put("/books/999", json={
        "title": "Updated",
        "publication_year": 2020,
    })

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_book(client, book_service):
    book_service.delete_book.return_value = True

    response = await client.delete("/books/1")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_book_not_found(client, book_service):
    book_service.delete_book.return_value = False

    response = await client.delete("/books/999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_assign_authors(client, book_service):
    book_service.assign_authors_to_book.return_value = True

    response = await client.post("/books/1/authors", json={"author_ids": [1, 2]})

    assert response.status_code == 200
    assert response.json()["message"] == "Authors assigned successfully"


@pytest.mark.asyncio
async def test_assign_authors_book_not_found(client, book_service):
    book_service.assign_authors_to_book.side_effect = ValueError(
        "Book with id 999 not found"
    )

    response = await client.post("/books/999/authors", json={"author_ids": [1]})

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unassign_author(client, book_service):
    book_service.unassign_author_from_book.return_value = True

    response = await client.delete("/books/1/authors/10")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
