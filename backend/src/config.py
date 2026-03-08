from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


class AppConfig(BaseConfig):
    DB_HOST: Optional[str] = "localhost"
    DB_NAME: Optional[str] = "app"
    DB_USER: Optional[str] = "postgres"
    DB_PASSWORD: Optional[str] = "pass"


config = AppConfig()