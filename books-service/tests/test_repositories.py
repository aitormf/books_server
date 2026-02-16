from datetime import datetime

from app.domain.entities import Author, Book
from app.infrastructure.database.models import AuthorsCacheModel, BookModel
from app.infrastructure.database.repositories import PostgreSQLBookRepository


class TestEntityConversions:
    """Test ORM model to domain entity conversion methods."""

    def test_book_model_to_entity(self):
        repo = PostgreSQLBookRepository.__new__(PostgreSQLBookRepository)
        model = BookModel()
        model.id = 1
        model.title = "Test Book"
        model.isbn = "978-0000000001"
        model.publication_year = 2020
        model.created_at = datetime(2025, 1, 1)
        model.updated_at = datetime(2025, 1, 1)

        entity = repo._to_entity(model)

        assert isinstance(entity, Book)
        assert entity.id == 1
        assert entity.title == "Test Book"
        assert entity.isbn == "978-0000000001"
        assert entity.publication_year == 2020

    def test_author_cache_model_to_entity(self):
        repo = PostgreSQLBookRepository.__new__(PostgreSQLBookRepository)
        model = AuthorsCacheModel()
        model.author_id = 10
        model.name = "Test Author"
        model.nationality = "Spanish"

        entity = repo._author_to_entity(model)

        assert isinstance(entity, Author)
        assert entity.id == 10
        assert entity.name == "Test Author"
        assert entity.nationality == "Spanish"

    def test_book_entity_defaults(self):
        book = Book(id=None, title="Test")
        assert book.authors == []
        assert book.isbn is None
        assert book.publication_year is None

    def test_author_entity_defaults(self):
        author = Author(id=None, name="Test")
        assert author.nationality is None
