"""Configuration management for MCP search server."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    """Server configuration."""

    security_token: str = secrets.token_urlsafe(64)
    environment: Literal["production", "development", "test"] = "development"
    name: str = "MCP search server"
    host: str = "localhost"
    port: int = 8080


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"


class GeminiConfig(BaseModel):
    """Configuration for Gemini (external model/service) integration."""

    api_key: str
    embedding_model: str = "models/gemini-embedding-2-preview"


class QdrantConfig(BaseModel):
    host: str = "localhost"
    port: int = 6333


class Config(BaseSettings):
    """App configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="MCP_SEARCH__",
        env_ignore_empty=True,
    )

    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)


@lru_cache
def build_app_config() -> Config:
    """Build app configuration."""

    return Config()
