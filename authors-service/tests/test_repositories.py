from datetime import date, datetime

from app.domain.entities import Author, Book
from app.infrastructure.database.models import AuthorModel, BooksCacheModel
from app.infrastructure.database.repositories import PostgreSQLAuthorRepository


class TestEntityConversions:
    """Test ORM model to domain entity conversion methods."""

    def test_author_model_to_entity(self):
        repo = PostgreSQLAuthorRepository.__new__(PostgreSQLAuthorRepository)
        model = AuthorModel()
        model.id = 1
        model.name = "Test Author"
        model.birth_date = date(1990, 1, 1)
        model.nationality = "Spanish"
        model.created_at = datetime(2025, 1, 1)
        model.updated_at = datetime(2025, 1, 1)

        entity = repo._to_entity(model)

        assert isinstance(entity, Author)
        assert entity.id == 1
        assert entity.name == "Test Author"
        assert entity.birth_date == date(1990, 1, 1)
        assert entity.nationality == "Spanish"

    def test_book_cache_model_to_entity(self):
        repo = PostgreSQLAuthorRepository.__new__(PostgreSQLAuthorRepository)
        model = BooksCacheModel()
        model.book_id = 10
        model.title = "Test Book"
        model.isbn = "978-0000000001"
        model.publication_year = 2020

        entity = repo._book_to_entity(model)

        assert isinstance(entity, Book)
        assert entity.id == 10
        assert entity.title == "Test Book"
        assert entity.isbn == "978-0000000001"
        assert entity.publication_year == 2020

    def test_author_entity_defaults(self):
        author = Author(id=None, name="Test")
        assert author.books == []
        assert author.created_at is None

    def test_book_entity_defaults(self):
        book = Book(id=None, title="Test")
        assert book.isbn is None
        assert book.publication_year is None
