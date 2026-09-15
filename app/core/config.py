from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    EMAIL: str
    APP_PASSWORD: str
    GMAIL_FOLDER: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    N8N_WEBHOOK_SECRET: str
    CRON_ENABLED: bool = True
    CRON_SCHEDULE: str = "30 4 * * *"
    CRON_TIMEZONE: str = "Asia/Kolkata"
    CRON_LOOKBACK_DAYS: int = 1

    @field_validator("JWT_ALGORITHM")
    @classmethod
    def normalize_jwt_algorithm(cls, value: str) -> str:
        return value.strip().upper()

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
