from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://devuser:devpassword@localhost:5433/saas_dev"

    # Redis (for ARQ job queue)
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Environment
    ENVIRONMENT: str = "development"

    # AI Generation
    AI_MODEL: str = "gpt-4o"
    AI_TEMPERATURE: float = 0.7
    GENERATION_SOFT_CAP: float = 500.0  # $500 default soft cap

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
