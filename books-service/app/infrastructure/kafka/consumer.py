import asyncio
import json

import structlog
from aiokafka import AIOKafkaConsumer
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.config import settings
from app.infrastructure.database.connection import async_session_factory
from app.infrastructure.database.models import AuthorsCacheModel, BookAuthorModel

logger = structlog.get_logger()

TOPICS = [
    "author.created",
    "author.updated",
    "author.deleted",
    "author_book.linked",
    "author_book.unlinked",
]

MAX_RETRIES = 3


async def handle_author_created_or_updated(data: dict, session) -> None:
    """Upsert author into local cache (idempotent)."""
    stmt = pg_insert(AuthorsCacheModel).values(
        author_id=data["author_id"],
        name=data["name"],
        nationality=data.get("nationality"),
    ).on_conflict_do_update(
        index_elements=["author_id"],
        set_={
            "name": data["name"],
            "nationality": data.get("nationality"),
        },
    )
    await session.execute(stmt)
    await session.commit()


async def handle_author_deleted(data: dict, session) -> None:
    """Remove author from cache and all relationships."""
    author_id = data["author_id"]
    await session.execute(
        delete(BookAuthorModel).where(BookAuthorModel.author_id == author_id)
    )
    await session.execute(
        delete(AuthorsCacheModel).where(AuthorsCacheModel.author_id == author_id)
    )
    await session.commit()


async def handle_author_book_linked(data: dict, session) -> None:
    """Sync relationship created by the authors service."""
    stmt = pg_insert(BookAuthorModel).values(
        book_id=data["book_id"],
        author_id=data["author_id"],
    ).on_conflict_do_nothing()
    await session.execute(stmt)
    await session.commit()


async def handle_author_book_unlinked(data: dict, session) -> None:
    """Sync relationship removal from the authors service."""
    await session.execute(
        delete(BookAuthorModel).where(
            BookAuthorModel.book_id == data["book_id"],
            BookAuthorModel.author_id == data["author_id"],
        )
    )
    await session.commit()


EVENT_HANDLERS = {
    "author.created": handle_author_created_or_updated,
    "author.updated": handle_author_created_or_updated,
    "author.deleted": handle_author_deleted,
    "author_book.linked": handle_author_book_linked,
    "author_book.unlinked": handle_author_book_unlinked,
}


async def process_message(message) -> None:
    """Process a single Kafka message with retry logic."""
    try:
        payload = json.loads(message.value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.error("invalid_message_format", topic=message.topic)
        return

    event_type = payload.get("event_type", message.topic)
    data = payload.get("data", {})
    correlation_id = payload.get("correlation_id", "unknown")

    handler = EVENT_HANDLERS.get(event_type)
    if not handler:
        logger.warning("unknown_event_type", event_type=event_type)
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with async_session_factory() as session:
                await handler(data, session)
            logger.info(
                "kafka_event_processed",
                event_type=event_type,
                correlation_id=correlation_id,
            )
            return
        except Exception:
            logger.error(
                "kafka_event_processing_failed",
                event_type=event_type,
                attempt=attempt,
                exc_info=True,
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2**attempt)

    logger.error(
        "kafka_event_dead_letter",
        event_type=event_type,
        data=data,
    )


async def start_consumer() -> None:
    """Start the Kafka consumer loop with reconnection logic."""
    consumer = None
    while True:
        try:
            consumer = AIOKafkaConsumer(
                *TOPICS,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=f"{settings.service_name}-group",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            await consumer.start()
            logger.info("kafka_consumer_started", topics=TOPICS)

            async for message in consumer:
                await process_message(message)
        except asyncio.CancelledError:
            logger.info("kafka_consumer_cancelled")
            break
        except Exception:
            logger.error("kafka_consumer_error", exc_info=True)
            await asyncio.sleep(5)
        finally:
            if consumer:
                try:
                    await consumer.stop()
                except Exception:
                    pass
