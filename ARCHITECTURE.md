# Architecture Documentation

## Overview

This system follows a **microservices architecture** with two independent services communicating asynchronously via Apache Kafka. Each service owns its data and maintains local caches of data from the other service for fast reads.

## Architecture Patterns

### 1. Microservices with Database-per-Service

Each microservice has its own logical database within a shared PostgreSQL instance:

```
PostgreSQL Instance
├── authors_db (owned by Authors Service)
│   ├── authors          — Primary author data
│   ├── author_books     — Author-to-book relationships
│   └── books_cache      — Local cache of book data from Books Service
│
└── books_db (owned by Books Service)
    ├── books            — Primary book data
    ├── book_authors     — Book-to-author relationships
    └── authors_cache    — Local cache of author data from Authors Service
```

**Why a single PostgreSQL instance?** Cost and resource efficiency for development and small deployments, while maintaining logical separation. Each service connects only to its own database.

### 2. Event-Driven Architecture

Services communicate exclusively through Kafka events. No synchronous HTTP calls between services.

```
Authors Service                    Books Service
      │                                  │
      ├── author.created ──────────────> │ (updates authors_cache)
      ├── author.updated ──────────────> │ (updates authors_cache)
      ├── author.deleted ──────────────> │ (removes from cache)
      ├── author_book.linked ──────────> │ (syncs book_authors)
      ├── author_book.unlinked ────────> │ (syncs book_authors)
      │                                  │
      │ <────────────── book.created ────┤
      │ <────────────── book.updated ────┤
      │ <────────────── book.deleted ────┤
      │ <────── book_author.linked ──────┤
      │ <────── book_author.unlinked ────┤
```

**Why Kafka instead of REST?**
- **Decoupling**: Services don't need to know each other's locations
- **Resilience**: If one service is down, events are buffered in Kafka
- **Eventual consistency**: Both services maintain their own view of the data
- **Scalability**: Services can be scaled independently

### 3. Layered Architecture with Repository Pattern

Each service follows a strict layered architecture:

```
┌──────────────────────────────────────┐
│         API Layer (FastAPI)          │
│  routes.py, schemas.py              │
│  HTTP concerns only                 │
├──────────────────────────────────────┤
│       Domain Layer (Business)        │
│  services.py, entities.py           │
│  Pure Python, no framework deps     │
├──────────────────────────────────────┤
│     Repository Layer (Contracts)     │
│  interfaces.py (ABC)                │
│  Abstract persistence contracts     │
├──────────────────────────────────────┤
│   Infrastructure Layer (Details)     │
│  database/, kafka/                  │
│  SQLAlchemy, aiokafka               │
└──────────────────────────────────────┘
```

**Key rules:**
- Routes never import SQLAlchemy models
- Services only depend on abstract interfaces (ABC)
- Domain entities are plain Python dataclasses
- Only the infrastructure layer knows about ORMs and databases

### 4. Dependency Injection

The `dependencies.py` module is the single point where interfaces are connected to implementations:

```python
# Current: PostgreSQL
author_repo = PostgreSQLAuthorRepository(session)

# Future: MongoDB (only this file changes)
# author_repo = MongoDBAuthorRepository(mongo_client)
```

## Event Message Format

All Kafka messages follow a standard envelope:

```json
{
  "event_type": "author.created",
  "event_id": "uuid-v4",
  "timestamp": "2025-02-14T10:30:00+00:00",
  "correlation_id": "request-uuid",
  "data": {
    "author_id": 1,
    "name": "Gabriel Garcia Marquez",
    "nationality": "Colombian"
  }
}
```

## Eventual Consistency

This system embraces **eventual consistency**. When an author is created:

1. Authors Service creates the author in `authors_db`
2. Authors Service publishes `author.created` to Kafka
3. Books Service consumes the event and updates `authors_cache`

There is a brief window where the Books Service doesn't yet know about the new author. This is acceptable because:
- Each service is independently functional
- The caches are self-healing (new events overwrite stale data)
- Idempotent consumers handle duplicate or redelivered messages

## Idempotency

All Kafka consumers use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (upsert) to ensure:
- Duplicate messages don't create duplicate data
- Out-of-order messages resolve to the latest state
- Consumers can be safely restarted from any offset

## Error Handling

- **HTTP errors**: Standardized JSON responses with correlation IDs
- **Kafka consumer failures**: 3 retries with exponential backoff
- **Dead letter logging**: Failed messages are logged for investigation
- **Global exception handler**: Catches unhandled errors at the FastAPI level

## Observability

- **Structured logging**: All logs are JSON via structlog
- **Correlation IDs**: Propagated through HTTP headers and Kafka messages
- **Request timing**: Every HTTP request logs duration in milliseconds
- **Event tracking**: Every published/consumed Kafka event is logged

## Data Flow: Assigning Books to an Author

```
Client                Authors Service              Kafka              Books Service
  │                        │                         │                      │
  ├─POST /authors/1/books─>│                         │                      │
  │                        ├─validate author exists───│                      │
  │                        ├─validate books in cache──│                      │
  │                        ├─insert author_books──────│                      │
  │                        ├─publish author_book.linked─>│                   │
  │                        │                         │──>consume event──────>│
  │<────200 OK─────────────┤                         │   insert book_authors│
  │                        │                         │                      │
```

## Testing Strategy

- **Unit tests**: Mock repositories to test business logic in isolation
- **Route tests**: Override FastAPI dependencies with mocked services
- **Repository tests**: Test entity conversion methods
- **No integration tests requiring running infrastructure** — by design, the Repository Pattern makes unit tests sufficient for business logic validation
