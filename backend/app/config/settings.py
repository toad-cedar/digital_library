from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

from pathlib import Path
from urllib.parse import quote_plus
from functools import lru_cache

class Settings(BaseSettings):
  POSTGRES_USER: str = Field(..., alias='DB_USER')
  POSTGRES_PASSWORD: str = Field(..., alias='DB_PASSWORD')
  POSTGRES_HOST: str = Field(default='localhost', alias='DB_HOST')
  POSTGRES_PORT: int = Field(default=5432, alias='DB_PORT')
  DATABASE_NAME: str = Field(default='library_db', alias='DB_NAME')
  
  SECRET_KEY: str = Field(..., alias='SECRET_KEY')  
  
  MINIO_USER: str = Field(..., alias='MINIO_ROOT_USER')
  MINIO_PASSWORD: str = Field(..., alias='MINIO_ROOT_PASSWORD')
  MINIO_ENDPOINT: str = Field(default='localhost:9000', alias='MINIO_ENDPOINT')
  MINIO_ACCESS_KEY: str = Field(..., alias='MINIO_ACCESS_KEY')
  MINIO_SECRET_KEY: str = Field(..., alias='MINIO_SECRET_KEY')
  MINIO_BUCKET: str = Field(default='documents', alias='MINIO_BUCKET')

  REDIS_USER: str = Field(..., alias='REDIS_USER')
  REDIS_PASSWORD: str = Field(..., alias='REDIS_PASSWORD')
  REDIS_HOST: str = Field(default='localhost', alias='REDIS_HOST')
  REDIS_PORT: int = Field(default=6379, alias='REDIS_PORT')
  
  ELASTICSEARCH_PASSWORD: str = Field(..., alias='ELASTIC_PASSWORD')
  ELASTICSEARCH_HOST: str = Field(default='localhost', alias='ELASTICSEARCH_HOST')
  ELASTICSEARCH_PORT: int = Field(default=9200, alias='ELASTICSEARCH_PORT')
  
  ALLOWED_ORIGINS: list[str] = Field(
    default=["http://localhost:5173"],
    alias="ALLOWED_ORIGINS",
    description="Разрешённые CORS-источники"
  )
  
  
  model_config = SettingsConfigDict(
    env_file=Path(__file__).resolve().parents[3] / '.env',
    env_file_encoding='utf-8',
    case_sensitive=False,
    extra='ignore',
  )
  
  @computed_field
  @property
  def get_async_db_url(self) -> str:
    """Для SQLAlchemy"""
    user = quote_plus(self.POSTGRES_USER)
    password = quote_plus(self.POSTGRES_PASSWORD)
    return (
      f'postgresql+asyncpg://{user}:{password}@'
      f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.DATABASE_NAME}'
    )
    
  @computed_field
  @property
  def get_sync_db_url(self) -> str:
    """Для Alembic-миграций (psycopg2)"""
    user = quote_plus(self.POSTGRES_USER)
    password = quote_plus(self.POSTGRES_PASSWORD)
    return (
      f'postgresql://{user}:{password}@'
      f'{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.DATABASE_NAME}'
    )
  
  @computed_field
  @property
  def get_redis_url(self) -> str:
    user = quote_plus(self.REDIS_USER)
    password = quote_plus(self.REDIS_PASSWORD)
    return (
      f'redis://{user}:{password}@{self.REDIS_HOST}:{self.REDIS_PORT}/0' 
    )

@lru_cache
def get_settings() -> Settings:
  return Settings()