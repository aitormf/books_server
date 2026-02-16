from datetime import date
from unittest.mock import AsyncMock, call

import pytest

from app.domain.entities import Author, Book
from app.domain.services import AuthorService


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
    return AuthorService(
        author_repo=repo,
        books_cache=cache,
        event_publisher=publisher,
        commit=commit,
    )


@pytest.fixture
def sync_service(_mocks):
    repo, cache, _, commit = _mocks
    return AuthorService(
        author_repo=repo,
        books_cache=cache,
        event_publisher=None,
        commit=commit,
    )


# ── create ──


@pytest.mark.asyncio
async def test_create_commits_once(service):
    author = Author(id=None, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.create.return_value = Author(
        id=1, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES"
    )

    await service.create_author(author)

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_no_commit_on_repo_failure(service):
    author = Author(id=None, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.create.side_effect = RuntimeError("db error")

    with pytest.raises(RuntimeError):
        await service.create_author(author)

    service._commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_publishes_after_commit(service):
    author = Author(id=None, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES")
    service.author_repo.create.return_value = Author(
        id=1, name="Test Author", birth_date=date(1990, 1, 1), nationality="ES"
    )

    call_order = []
    service._commit.side_effect = lambda: call_order.append("commit")
    service.event_publisher.publish.side_effect = lambda *a, **kw: call_order.append("publish")

    await service.create_author(author)

    assert call_order == ["commit", "publish"]


# ── update ──


@pytest.mark.asyncio
async def test_update_commits_once(service):
    author = Author(id=1, name="Updated", birth_date=date(1990, 1, 1), nationality="FR")
    service.author_repo.update.return_value = author

    await service.update_author(1, author)

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_nonexistent_no_commit(service):
    author = Author(id=1, name="Updated", birth_date=date(1990, 1, 1), nationality="FR")
    service.author_repo.update.return_value = None

    await service.update_author(999, author)

    service._commit.assert_not_called()


# ── delete ──


@pytest.mark.asyncio
async def test_delete_commits_once(service):
    service.author_repo.get_by_id.return_value = Author(
        id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES"
    )
    service.author_repo.delete.return_value = True

    await service.delete_author(1)

    service._commit.assert_called_once()


# ── assign ──


@pytest.mark.asyncio
async def test_assign_single_commit(service):
    service.author_repo.get_by_id.return_value = Author(
        id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES"
    )
    service.books_cache.get_book.side_effect = [
        Book(id=10, title="B1"),
        Book(id=20, title="B2"),
        Book(id=30, title="B3"),
    ]
    service.author_repo.add_books.return_value = True

    await service.assign_books_to_author(1, [10, 20, 30])

    service._commit.assert_called_once()


@pytest.mark.asyncio
async def test_assign_no_commit_on_validation_failure(service):
    service.author_repo.get_by_id.return_value = Author(
        id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES"
    )
    service.books_cache.get_book.return_value = None

    with pytest.raises(ValueError, match="not found in cache"):
        await service.assign_books_to_author(1, [100])

    service._commit.assert_not_called()


# ── unassign ──


@pytest.mark.asyncio
async def test_unassign_commits_once(service):
    service.author_repo.get_by_id.return_value = Author(
        id=1, name="Test", birth_date=date(1990, 1, 1), nationality="ES"
    )
    service.author_repo.remove_book.return_value = True

    await service.unassign_book_from_author(1, 10)

    service._commit.assert_called_once()


# ── sync: remove from cache (atomic multi-op) ──


@pytest.mark.asyncio
async def test_sync_remove_from_cache_atomic(sync_service):
    await sync_service.remove_book_from_cache_and_authors(book_id=42)

    sync_service.author_repo.remove_book_from_all_authors.assert_called_once_with(42)
    sync_service.books_cache.delete_book.assert_called_once_with(42)
    sync_service._commit.assert_called_once()
