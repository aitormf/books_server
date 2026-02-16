from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "postgresql+asyncpg://library_user:library_pass_2025@postgres:5432/books_db"
    kafka_bootstrap_servers: str = "kafka:9092"
    service_name: str = "books-service"
    service_port: int = 8002
    log_level: str = "INFO"
    environment: str = "development"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
