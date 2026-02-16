from unittest.mock import AsyncMock, call

import pytest

from app.domain.entities import Author, Book
from app.domain.services import BookService


@pytest.fixture
def _mocks():
    repo = AsyncMock()
    cache = AsyncMock()
    publisher = AsyncMock()
    commit = AsyncMock()
    return repo, cache, publisher, commit


@pytest.fixture
def service(_mocks):
    repo, cache, publisher, commit = _mocks
    return BookService(
        book_repo=repo,
        authors_cache=cache,
        event_publisher=publisher,
        commit=commit,
    )


@pytest.fixture
def sync_service(_mocks):
    repo, cache, _, commit = _mocks
    return BookService(
        book_repo=repo,
        authors_cache=cache,
        event_publisher=None,
        commit=commit,
    )


# ── create ──


@pytest.mark.asyncio
async def test_create_commits_once(service):
    book = Book(id=None, title="Test Book", isbn="123", publication_year=2020)
    service.book_repo.create.return_value = Book(
        id=1, title="Test Book", isbn="123", publication_year=2020
    )

    await service.create_book(book)

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_no_commit_on_repo_failure(service):
    book = Book(id=None, title="Test Book", isbn="123", publication_year=2020)
    service.book_repo.create.side_effect = RuntimeError("db error")

    with pytest.raises(RuntimeError):
        await service.create_book(book)

    service._commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_publishes_after_commit(service):
    book = Book(id=None, title="Test Book", isbn="123", publication_year=2020)
    service.book_repo.create.return_value = Book(
        id=1, title="Test Book", isbn="123", publication_year=2020
    )

    call_order = []
    service._commit.side_effect = lambda: call_order.append("commit")
    service.event_publisher.publish.side_effect = lambda *a, **kw: call_order.append("publish")

    await service.create_book(book)

    assert call_order == ["commit", "publish"]


# ── update ──


@pytest.mark.asyncio
async def test_update_commits_once(service):
    book = Book(id=1, title="Updated", isbn="999", publication_year=2025)
    service.book_repo.update.return_value = book

    await service.update_book(1, book)

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_no_commit(service):
    book = Book(id=1, title="Updated", isbn="999", publication_year=2025)
    service.book_repo.update.return_value = None

    await service.update_book(999, book)

    service._commit.assert_not_called()


# ── delete ──


@pytest.mark.asyncio
async def test_delete_commits_once(service):
    service.book_repo.get_by_id.return_value = Book(
        id=1, title="Test", publication_year=2020
    )
    service.book_repo.delete.return_value = True

    await service.delete_book(1)

    service._commit.assert_called_once()


# ── assign ──


@pytest.mark.asyncio
async def test_assign_single_commit(service):
    service.book_repo.get_by_id.return_value = Book(
        id=1, title="Test", publication_year=2020
    )
    service.authors_cache.get_author.side_effect = [
        Author(id=10, name="A1"),
        Author(id=20, name="A2"),
        Author(id=30, name="A3"),
    ]
    service.book_repo.add_authors.return_value = True

    await service.assign_authors_to_book(1, [10, 20, 30])

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_assign_no_commit_on_validation_failure(service):
    service.book_repo.get_by_id.return_value = Book(
        id=1, title="Test", publication_year=2020
    )
    service.authors_cache.get_author.return_value = None

    with pytest.raises(ValueError, match="not found in cache"):
        await service.assign_authors_to_book(1, [100])

    service._commit.assert_not_called()


# ── unassign ──


@pytest.mark.asyncio
async def test_unassign_commits_once(service):
    service.book_repo.get_by_id.return_value = Book(
        id=1, title="Test", publication_year=2020
    )
    service.book_repo.remove_author.return_value = True

    await service.unassign_author_from_book(1, 10)

    service._commit.assert_called_once()


# ── sync: remove from cache (atomic multi-op) ──


@pytest.mark.asyncio
async def test_sync_remove_from_cache_atomic(sync_service):
    await sync_service.remove_author_from_cache_and_books(author_id=42)

    sync_service.book_repo.remove_author_from_all_books.assert_called_once_with(42)
    sync_service.authors_cache.delete_author.assert_called_once_with(42)
    sync_service._commit.assert_called_once()
