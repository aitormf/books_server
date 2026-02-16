from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session():
    """FastAPI dependency that provides a database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def create_tables() -> None:
    """Create all tables defined in the ORM models."""
    from app.infrastructure.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
