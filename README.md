# Book Management System

A microservices-based system for managing books and authors, built with Python, FastAPI, Kafka, and PostgreSQL.

## Architecture

- **Authors Service** (port 8001) — CRUD operations for authors
- **Books Service** (port 8002) — CRUD operations for books
- **Kafka (KRaft)** — Asynchronous event-driven communication between services
- **PostgreSQL** — Single instance with two isolated databases (`authors_db`, `books_db`)

Each service follows a **layered architecture** with the **Repository Pattern** to fully decouple business logic from persistence. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Tech Stack

- Python 3.13
- FastAPI + Uvicorn
- SQLAlchemy (async) + asyncpg
- Apache Kafka (KRaft mode, no Zookeeper)
- PostgreSQL 16
- Docker Compose
- uv (package manager)
- structlog (structured JSON logging)

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd book-management-system

# 2. Start all services
docker-compose up -d

# 3. Verify everything is running
docker-compose ps

# 4. Check logs
docker-compose logs -f authors-service books-service
```

## API Usage Examples

### Create an author

```bash
curl -X POST http://localhost:8001/authors \
  -H "Content-Type: application/json" \
  -d '{"name": "Gabriel Garcia Marquez", "birth_date": "1927-03-06", "nationality": "Colombian"}'
```

### Create books

```bash
curl -X POST http://localhost:8002/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Cien anos de soledad", "isbn": "978-0060883287", "publication_year": 1967}'

curl -X POST http://localhost:8002/books \
  -H "Content-Type: application/json" \
  -d '{"title": "El amor en los tiempos del colera", "isbn": "978-0307389732", "publication_year": 1985}'
```

### Assign books to an author

```bash
curl -X POST http://localhost:8001/authors/1/books \
  -H "Content-Type: application/json" \
  -d '{"book_ids": [1, 2]}'
```

### Get author with books

```bash
curl http://localhost:8001/authors/1
```

### Get book with authors

```bash
curl http://localhost:8002/books/1
```

## API Endpoints

### Authors Service (port 8001)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/authors` | Create an author |
| GET | `/authors` | List authors (`?skip=0&limit=100`) |
| GET | `/authors/{id}` | Get author with books |
| PUT | `/authors/{id}` | Update author |
| DELETE | `/authors/{id}` | Delete author |
| POST | `/authors/{id}/books` | Assign books |
| DELETE | `/authors/{id}/books/{book_id}` | Unassign book |
| GET | `/health` | Health check |

### Books Service (port 8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/books` | Create a book |
| GET | `/books` | List books (`?skip=0&limit=100`) |
| GET | `/books/{id}` | Get book with authors |
| PUT | `/books/{id}` | Update book |
| DELETE | `/books/{id}` | Delete book |
| POST | `/books/{id}/authors` | Assign authors |
| DELETE | `/books/{id}/authors/{author_id}` | Unassign author |
| GET | `/health` | Health check |

## API Documentation

Once running, interactive docs are available at:

- Authors: http://localhost:8001/docs
- Books: http://localhost:8002/docs

## Running Tests

```bash
# Install dev dependencies locally
cd authors-service && uv pip install -e ".[dev]" && cd ..
cd books-service && uv pip install -e ".[dev]" && cd ..

# Run tests
cd authors-service && pytest && cd ..
cd books-service && pytest && cd ..

# Run with coverage
cd authors-service && pytest --cov=app --cov-report=term-missing && cd ..
```

## Kafka Topics

Events published/consumed for eventual consistency:

| Topic | Publisher | Consumer |
|-------|-----------|----------|
| `author.created` | Authors | Books |
| `author.updated` | Authors | Books |
| `author.deleted` | Authors | Books |
| `book.created` | Books | Authors |
| `book.updated` | Books | Authors |
| `book.deleted` | Books | Authors |
| `author_book.linked` | Authors | Books |
| `author_book.unlinked` | Authors | Books |
| `book_author.linked` | Books | Authors |
| `book_author.unlinked` | Books | Authors |

## Environment Variables

See [.env.example](.env.example) for all configurable values.

## Useful Commands

```bash
# Rebuild without cache
docker-compose build --no-cache

# Access PostgreSQL
docker-compose exec postgres psql -U library_user -d authors_db

# List Kafka topics
docker-compose exec kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# Consume messages for debugging
docker-compose exec kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic author.created \
  --from-beginning
```

## Troubleshooting

**Services fail to start**: Ensure Kafka and PostgreSQL are healthy first:
```bash
docker-compose ps  # Check health status
docker-compose logs kafka  # Check Kafka logs
```

**Kafka connection errors**: Kafka may take 30-45 seconds to start. Services will retry automatically.

**Database connection errors**: Verify PostgreSQL is running and the init script created both databases:
```bash
docker-compose exec postgres psql -U library_user -c "\l"
```

**Books not appearing on author**: Kafka events are eventually consistent. Wait a moment for the consumer to sync.
