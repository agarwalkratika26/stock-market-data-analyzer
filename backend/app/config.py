from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Stock Market Data Analyzer"
    api_prefix: str = "/api"
    data_dir: Path = Path(__file__).resolve().parents[1] / "data"
    cors_origins: str = "http://localhost:3000"
    default_provider: str = "demo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
