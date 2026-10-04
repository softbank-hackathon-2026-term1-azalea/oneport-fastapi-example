from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_name: str = "notes"
    port: int = 8080
    log_format: Literal["json", "text"] = "json"
    log_level: str = "INFO"
    docs_enabled: bool = False

    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "notes"
    db_user: str = "notes"
    db_password: SecretStr = SecretStr("")

    redis_url: str | None = None

    app_force_unhealthy: bool = False
    launchpad_release_id: str | None = None
    app_color: str = "#2da44e"

    @property
    def sqlalchemy_url(self) -> URL:
        if self.database_url:
            url = make_url(self.database_url)
            if url.drivername in ("postgres", "postgresql"):
                url = url.set(drivername="postgresql+psycopg")
            return url
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value() or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
