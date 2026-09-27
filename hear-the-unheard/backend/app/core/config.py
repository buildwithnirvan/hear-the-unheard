"""
Application configuration, loaded from environment variables (see .env.example).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Hear the Unheard"
    environment: str = "development"

    # MongoDB only — see docs/STATUS.md for why. Local dev defaults to a
    # local mongod on the default port; docker-compose overrides this to
    # point at the `mongo` service.
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "hear_the_unheard"

    secret_key: str = "dev-only-change-me-before-any-real-deployment"
    access_token_expire_minutes: int = 60 * 12

    # Model management: which recognition model version is currently active.
    # None means "no trained ISL recognition model is loaded" — the API
    # will report this honestly rather than faking predictions (§10, §32).
    active_isl_model_version: str | None = None

    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
