from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Author, Book
from app.domain.services import BookService


@pytest.fixture
def service():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    mock_publisher = AsyncMock()
    return BookService(
        book_repo=mock_repo,
        authors_cache=mock_cache,
        event_publisher=mock_publisher,
    )


@pytest.mark.asyncio
async def test_create_book_validates_empty_title(service):
    book = Book(id=None, title="", publication_year=2020)
    with pytest.raises(ValueError, match="must not be empty"):
        await service.create_book(book)
    service.book_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_book_success(service):
    book = Book(id=None, title="Test Book", isbn="123", publication_year=2020)
    expected = Book(id=1, title="Test Book", isbn="123", publication_year=2020)
    service.book_repo.create.return_value = expected

    result = await service.create_book(book)

    assert result.id == 1
    assert result.title == "Test Book"
    service.book_repo.create.assert_called_once_with(book)
    service.event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_publishes_event(service):
    book = Book(id=None, title="Test Book", isbn="123", publication_year=2020)
    created = Book(id=1, title="Test Book", isbn="123", publication_year=2020)
    service.book_repo.create.return_value = created

    await service.create_book(book, correlation_id="test-456")

    service.event_publisher.publish.assert_called_once_with(
        "book.created",
        {
            "book_id": 1,
            "title": "Test Book",
            "isbn": "123",
            "publication_year": 2020,
        },
        "test-456",
    )


@pytest.mark.asyncio
async def test_get_book_with_authors(service):
    book = Book(id=1, title="Test Book", publication_year=2020)
    authors = [Author(id=1, name="Author 1"), Author(id=2, name="Author 2")]
    service.book_repo.get_by_id.return_value = book
    service.book_repo.get_authors_by_book.return_value = authors

    result = await service.get_book_with_authors(1)

    assert result is not None
    assert len(result.authors) == 2
    assert result.authors[0].name == "Author 1"


@pytest.mark.asyncio
async def test_get_book_not_found(service):
    service.book_repo.get_by_id.return_value = None
    result = await service.get_book_with_authors(999)
    assert result is None


@pytest.mark.asyncio
async def test_delete_book_publishes_event(service):
    book = Book(id=1, title="Test", publication_year=2020)
    service.book_repo.get_by_id.return_value = book
    service.book_repo.delete.return_value = True

    result = await service.delete_book(1, correlation_id="del-456")

    assert result is True
    service.event_publisher.publish.assert_called_once_with(
        "book.deleted",
        {"book_id": 1},
        "del-456",
    )


@pytest.mark.asyncio
async def test_delete_nonexistent_book(service):
    service.book_repo.get_by_id.return_value = None
    result = await service.delete_book(999)
    assert result is False
    service.event_publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_assign_authors_validates_book_exists(service):
    service.book_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Book with id 999 not found"):
        await service.assign_authors_to_book(999, [1, 2])


@pytest.mark.asyncio
async def test_assign_authors_validates_author_in_cache(service):
    book = Book(id=1, title="Test", publication_year=2020)
    service.book_repo.get_by_id.return_value = book
    service.authors_cache.get_author.return_value = None

    with pytest.raises(ValueError, match="Author with id 100 not found"):
        await service.assign_authors_to_book(1, [100])


@pytest.mark.asyncio
async def test_assign_authors_publishes_events(service):
    book = Book(id=1, title="Test", publication_year=2020)
    author1 = Author(id=10, name="Author 10")
    author2 = Author(id=20, name="Author 20")
    service.book_repo.get_by_id.return_value = book
    service.authors_cache.get_author.side_effect = [author1, author2]
    service.book_repo.add_authors.return_value = True

    await service.assign_authors_to_book(1, [10, 20], correlation_id="link-456")

    assert service.event_publisher.publish.call_count == 2


@pytest.mark.asyncio
async def test_update_book_success(service):
    book = Book(id=1, title="Updated Title", isbn="999", publication_year=2025)
    service.book_repo.update.return_value = book

    result = await service.update_book(1, book)

    assert result.title == "Updated Title"
    service.event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_book(service):
    book = Book(id=1, title="Updated", publication_year=2020)
    service.book_repo.update.return_value = None

    result = await service.update_book(999, book)

    assert result is None
    service.event_publisher.publish.assert_not_called()
