from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.domain.entities import Author, Book
from app.domain.services import AuthorService


@pytest.fixture
def service():
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    mock_publisher = AsyncMock()
    return AuthorService(
        author_repo=mock_repo,
        books_cache=mock_cache,
        event_publisher=mock_publisher,
        commit=AsyncMock(),
    )


@pytest.fixture
def sync_service():
    """Service without event publisher, as used by Kafka handlers."""
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    return AuthorService(
        author_repo=mock_repo,
        books_cache=mock_cache,
        event_publisher=None,
        commit=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_create_author_validates_short_name(service):
    author = Author(id=None, name="A", birth_date=date(1990, 1, 1), nationality="ES")
    with pytest.raises(ValueError, match="at least 2 characters"):
        await service.create_author(author)
    service.author_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_author_validates_empty_name(service):
    author = Author(id=None, name="", birth_date=date(1990, 1, 1), nationality="ES")
    with pytest.raises(ValueError, match="at least 2 characters"):
        await service.create_author(author)


@pytest.mark.asyncio
async def test_create_author_success(service):
    author = Author(id=None, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    expected = Author(id=1, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.create.return_value = expected

    result = await service.create_author(author)

    assert result.id == 1
    assert result.name == "Test Author"
    service.author_repo.create.assert_called_once_with(author)
    service.event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_create_author_publishes_event(service):
    author = Author(id=None, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    created = Author(id=1, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.create.return_value = created

    await service.create_author(author, correlation_id="test-123")

    service.event_publisher.publish.assert_called_once_with(
        "author.created",
        {
            "author_id": 1,
            "name": "Test Author",
            "birth_date": "1990-01-01",
            "nationality": "ES",
        },
        "test-123",
    )


@pytest.mark.asyncio
async def test_get_author_with_books(service):
    author = Author(id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES")
    books = [Book(id=1, title="Book 1"), Book(id=2, title="Book 2")]
    service.author_repo.get_by_id.return_value = author
    service.author_repo.get_books_by_author.return_value = books

    result = await service.get_author_with_books(1)

    assert result is not None
    assert len(result.books) == 2
    assert result.books[0].title == "Book 1"


@pytest.mark.asyncio
async def test_get_author_not_found(service):
    service.author_repo.get_by_id.return_value = None
    result = await service.get_author_with_books(999)
    assert result is None


@pytest.mark.asyncio
async def test_delete_author_publishes_event(service):
    author = Author(id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.get_by_id.return_value = author
    service.author_repo.delete.return_value = True

    result = await service.delete_author(1, correlation_id="del-123")

    assert result is True
    service.event_publisher.publish.assert_called_once_with(
        "author.deleted",
        {"author_id": 1},
        "del-123",
    )


@pytest.mark.asyncio
async def test_delete_nonexistent_author(service):
    service.author_repo.get_by_id.return_value = None
    result = await service.delete_author(999)
    assert result is False
    service.event_publisher.publish.assert_not_called()


@pytest.mark.asyncio
async def test_assign_books_validates_author_exists(service):
    service.author_repo.get_by_id.return_value = None

    with pytest.raises(ValueError, match="Author with id 999 not found"):
        await service.assign_books_to_author(999, [1, 2])


@pytest.mark.asyncio
async def test_assign_books_validates_book_in_cache(service):
    author = Author(id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.get_by_id.return_value = author
    service.books_cache.get_book.return_value = None

    with pytest.raises(ValueError, match="Book with id 100 not found"):
        await service.assign_books_to_author(1, [100])


@pytest.mark.asyncio
async def test_assign_books_publishes_events(service):
    author = Author(id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES")
    book1 = Book(id=10, title="Book 10")
    book2 = Book(id=20, title="Book 20")
    service.author_repo.get_by_id.return_value = author
    service.books_cache.get_book.side_effect = [book1, book2]
    service.author_repo.add_books.return_value = True

    await service.assign_books_to_author(1, [10, 20], correlation_id="link-123")

    assert service.event_publisher.publish.call_count == 2


@pytest.mark.asyncio
async def test_update_author_success(service):
    author = Author(id=1, name="Updated Name", birth_date=date(1990, 1, 1), nationality="FR")
    service.author_repo.update.return_value = author

    result = await service.update_author(1, author)

    assert result.name == "Updated Name"
    service.event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_author(service):
    author = Author(id=1, name="Updated", birth_date=date(1990, 1, 1), nationality="FR")
    service.author_repo.update.return_value = None

    result = await service.update_author(999, author)

    assert result is None
    service.event_publisher.publish.assert_not_called()


# ── Sync method tests (Kafka handler delegation) ──


@pytest.mark.asyncio
async def test_sync_book_to_cache(sync_service):
    await sync_service.sync_book_to_cache(book_id=1, title="Test", isbn="123", year=2020)

    sync_service.books_cache.save_book.assert_called_once_with(
        book_id=1, title="Test", isbn="123", year=2020
    )


@pytest.mark.asyncio
async def test_remove_book_from_cache_and_authors(sync_service):
    await sync_service.remove_book_from_cache_and_authors(book_id=42)

    sync_service.author_repo.remove_book_from_all_authors.assert_called_once_with(42)
    sync_service.books_cache.delete_book.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_sync_book_linked(sync_service):
    await sync_service.sync_book_linked(author_id=1, book_id=10)

    sync_service.author_repo.add_books.assert_called_once_with(1, [10])


@pytest.mark.asyncio
async def test_sync_book_unlinked(sync_service):
    await sync_service.sync_book_unlinked(author_id=1, book_id=10)

    sync_service.author_repo.remove_book.assert_called_once_with(1, 10)
