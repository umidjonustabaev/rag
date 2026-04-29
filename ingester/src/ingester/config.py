from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class QdrantConfig(BaseModel):
    host: str = "localhost"
    port: int = 6333


class ConfluenceConfig(BaseModel):
    token: str
    base_url: str


class EmbeddingConfig(BaseModel):
    api_key: str
    model: str = "models/gemini-embedding-2-preview"
    dimensions: int = 3072
    chunk_size: int = 1024
    chunk_overlap: int = 256


class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"


class Config(BaseSettings):
    qdrant: QdrantConfig = QdrantConfig()
    confluence: ConfluenceConfig = Field(default_factory=ConfluenceConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="INGESTER__",
        env_ignore_empty=True
    )


@lru_cache
def get_app_config() -> Config:
    return Config()
