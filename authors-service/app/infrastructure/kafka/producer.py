import json
import uuid
from datetime import datetime, timezone

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings
from app.repositories.interfaces import IEventPublisher

logger = structlog.get_logger()


class KafkaProducerService(IEventPublisher):
    """Kafka event producer with structured message format."""

    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
        )
        await self._producer.start()
        logger.info("kafka_producer_started")

    async def stop(self) -> None:
        if self._producer:
            await self._producer.stop()
            logger.info("kafka_producer_stopped")

    async def publish(
        self, topic: str, data: dict, correlation_id: str | None = None
    ) -> None:
        if not self._producer:
            logger.warning("kafka_producer_not_started", topic=topic)
            return

        message = {
            "event_type": topic,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "data": data,
        }
        await self._producer.send_and_wait(topic, value=message)
        logger.info(
            "kafka_event_published",
            topic=topic,
            event_id=message["event_id"],
        )


kafka_producer = KafkaProducerService()
