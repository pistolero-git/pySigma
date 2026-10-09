from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "pySigma API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    api_key: str | None = None
    cors_origins: str = "*"
    max_sigma_bytes: int = 1_000_000

    model_config = SettingsConfigDict(env_prefix="PYSIGMA_", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if value == "*":
            return ["*"]
        return [origin.strip() for origin in value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
