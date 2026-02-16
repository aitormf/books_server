import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import router
from app.config import settings
from app.infrastructure.database.connection import create_tables, engine
from app.infrastructure.kafka.consumer import start_consumer
from app.infrastructure.kafka.producer import kafka_producer


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            service=settings.service_name,
        )

        start = time.time()
        try:
            response = await call_next(request)
        except Exception:
            logger.error("unhandled_request_error", exc_info=True)
            raise

        duration_ms = round((time.time() - start) * 1000, 2)
        logger.info(
            "http_request",
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        response.headers["X-Correlation-ID"] = correlation_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "starting_service",
        service=settings.service_name,
        port=settings.service_port,
    )
    await create_tables()
    await kafka_producer.start()
    consumer_task = asyncio.create_task(start_consumer())
    yield
    logger.info("stopping_service", service=settings.service_name)
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    await kafka_producer.stop()
    await engine.dispose()


app = FastAPI(
    title="Authors Service",
    description="Microservice for managing authors",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        "unhandled_exception",
        error=str(exc),
        correlation_id=correlation_id,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
        },
    )


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": settings.service_name}


app.include_router(router)
