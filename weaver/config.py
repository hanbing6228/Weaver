"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WEAVER_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "Weaver.AI Core Engine"
    api_prefix: str = "/api/v1"
    monte_carlo_runs: int = 10_000
    monte_carlo_seed: int | None = 42
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    static_client_dir: str = "client/dist"


settings = Settings()
