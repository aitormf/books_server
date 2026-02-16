import asyncio
import json

import structlog
from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.repositories.interfaces import EventHandler, IEventConsumer

logger = structlog.get_logger()

MAX_RETRIES = 3


class KafkaConsumerService(IEventConsumer):
    """Kafka event consumer that dispatches messages to registered handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, EventHandler] = {}
        self._task: asyncio.Task | None = None

    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type] = handler

    @property
    def _topics(self) -> list[str]:
        return list(self._handlers.keys())

    async def start(self) -> None:
        if not self._handlers:
            logger.warning("kafka_consumer_no_handlers")
            return
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _consume_loop(self) -> None:
        consumer = None
        while True:
            try:
                consumer = AIOKafkaConsumer(
                    *self._topics,
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    group_id=f"{settings.service_name}-group",
                    auto_offset_reset="earliest",
                    enable_auto_commit=True,
                )
                await consumer.start()
                logger.info("kafka_consumer_started", topics=self._topics)

                async for message in consumer:
                    await self._process_message(message)
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

    async def _process_message(self, message) -> None:
        try:
            payload = json.loads(message.value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.error("invalid_message_format", topic=message.topic)
            return

        event_type = payload.get("event_type", message.topic)
        data = payload.get("data", {})
        correlation_id = payload.get("correlation_id", "unknown")

        handler = self._handlers.get(event_type)
        if not handler:
            logger.warning("unknown_event_type", event_type=event_type)
            return

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await handler(data)
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
