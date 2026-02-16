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

### 3. Layered Architecture with Repository Pattern & Event Bus Abstraction

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
│    Contracts Layer (Interfaces)      │
│  interfaces.py (ABC)                │
│  IAuthorRepository, IBooksCache     │
│  IEventPublisher, IEventConsumer    │
├──────────────────────────────────────┤
│   Infrastructure Layer (Details)     │
│  database/  → SQLAlchemy, asyncpg   │
│  kafka/     → aiokafka              │
└──────────────────────────────────────┘
```

**Key rules:**
- Routes never import SQLAlchemy models or Kafka classes
- Services only depend on abstract interfaces (ABC)
- Domain entities are plain Python dataclasses
- Only the infrastructure layer knows about ORMs, databases, and message brokers

### 4. Event Bus Abstraction

The messaging layer mirrors the Repository Pattern applied to the database. Two abstract interfaces decouple all event-driven communication from the underlying message broker:

```python
class IEventPublisher(ABC):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def publish(self, topic: str, data: dict, correlation_id: str | None = None) -> None: ...

class IEventConsumer(ABC):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def register_handler(self, event_type: str, handler: EventHandler) -> None: ...
```

**Current implementation:** `KafkaProducerService` and `KafkaConsumerService` (using aiokafka).

**To switch to another broker** (e.g., RabbitMQ), create new classes implementing these interfaces — no changes needed in domain services, handlers, or API routes.

**Handler registration** is done at startup in `main.py`:

```python
kafka_consumer = KafkaConsumerService()
kafka_consumer.register_handler("book.created", handle_book_created_or_updated)
kafka_consumer.register_handler("book.updated", handle_book_created_or_updated)
# ...
```

Event handlers (`handlers.py`) are pure async functions with signature `async def handler(data: dict) -> None`. They delegate to the domain service layer — the same `AuthorService`/`BookService` used by HTTP routes — but instantiated **without an event publisher** to prevent cascading events. This ensures all data access goes through the domain layer regardless of the entry point:

```
HTTP    →  routes.py   →  DomainService(publisher=kafka)  →  Repository/Cache
Kafka   →  handlers.py →  DomainService(publisher=None)   →  Repository/Cache
```

Each handler receives a `service_factory` (async context manager) that creates a short-lived service with its own database session.

### 5. Dependency Injection

The `dependencies.py` module is the single point where interfaces are connected to implementations:

```python
# Current: PostgreSQL
author_repo = PostgreSQLAuthorRepository(session)

# Future: MongoDB (only this file changes)
# author_repo = MongoDBAuthorRepository(mongo_client)
```

The same applies to the event bus — `main.py` is where `KafkaProducerService` and `KafkaConsumerService` are instantiated and could be replaced.

## Event Message Format

All event messages follow a standard envelope (implemented by the publisher):

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

All event handlers use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (upsert) to ensure:
- Duplicate messages don't create duplicate data
- Out-of-order messages resolve to the latest state
- Consumers can be safely restarted from any offset

## Error Handling

- **HTTP errors**: Standardized JSON responses with correlation IDs
- **Event consumer failures**: 3 retries with exponential backoff
- **Dead letter logging**: Failed messages are logged for investigation
- **Global exception handler**: Catches unhandled errors at the FastAPI level

## Observability

- **Structured logging**: All logs are JSON via structlog
- **Correlation IDs**: Propagated through HTTP headers and Kafka messages
- **Request timing**: Every HTTP request logs duration in milliseconds
- **Event tracking**: Every published/consumed event is logged

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
