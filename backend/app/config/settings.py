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
  MINIO_REGION: str = Field(default='us', alias='MINIO_REGION')
  MINIO_SECURE: bool = Field(default=True, alias='MINIO_SECURE')
  VERIFY_TLS: bool = Field(default=True, alias='VERIFY_TLS')

  REDIS_USER: str = Field(..., alias='REDIS_USER')
  REDIS_PASSWORD: str = Field(..., alias='REDIS_PASSWORD')
  REDIS_HOST: str = Field(default='localhost', alias='REDIS_HOST')
  REDIS_PORT: int = Field(default=6379, alias='REDIS_PORT')
  REDIS_DB: str = Field(default='redis_db', alias='REDIS_DB')
  
  ELASTICSEARCH_USER: str = Field(..., alias='ELASTIC_USER')
  ELASTICSEARCH_PASSWORD: str = Field(..., alias='ELASTIC_PASSWORD')
  ELASTICSEARCH_HOST: str = Field(default='localhost', alias='ELASTIC_HOST')
  ELASTICSEARCH_PORT: int = Field(default=9200, alias='ELASTIC_PORT')
  ELASTICSEARCH_SECURE: bool = Field(default=True, alias='ELASTIC_SECURE')
  
  SMTP_USER: str = Field(..., alias='SMTP_USER')
  SMTP_PASSWORD: str = Field(..., alias='SMTP_PASSWORD')
  SMTP_HOST: str = Field(..., alias='SMTP_HOST')
  SMTP_PORT: int = Field(default=587, alias='SMTP_PORT')
  SMTP_USE_TLS: bool = Field(default=True, alias='SMTP_USE_TLS')
  
  TIKA_URL: str = Field(default="http://tika:9998", alias='TIKA_SERVER_URL')
  TIKA_TIMEOUT: int = Field(default=120, alias='TIKA_TIMEOUT')
  TIKA_JAR_PATH: str = Field(default='/opt/tika/tika-app.jar', alias='TIKA_JAR_PATH')
  TIKA_MAX_HEAP: str = Field(default='512m', alias='TIKA_MAX_PATH')
  
  OCR_MEMORY_LIMIT: int = Field(alias='OCR_MEMORY_LIMIT')
  MAX_UPLOAD_SIZE: int = Field(alias='MAX_UPLOAD_SIZE')
  RISK_WEIGHTS: dict = Field(
    default_factory=lambda: {
      "new_account_days": 20,      # аккаунт младше 7 дней
      "unknown_mime": 30,          # MIME не в белом списке
      "no_ocr_text": 15,           # не извлечён текст для PDF/изображений
      "hash_collision": 50,        # хеш совпадает с другим документом
      "large_file": 10,            # файл > 50 МБ
      "night_upload": 5,           # загрузка между 02:00-06:00
    },
    alias="RISK_WEIGHTS"
  )
  RISK_THRESHOLD_REJECT: int = Field(default=80, alias="RISK_THRESHOLD_REJECT")
  RISK_THRESHOLD_REVIEW: int = Field(default=30, alias="RISK_THRESHOLD_REVIEW")
  
  CONVERSION_TIMEOUT: int = Field(..., alias='CONVERSION_TIMEOUT')
  CONVERSION_MAX_PAGES: int = Field(..., alias='CONVERSION_MAX_PAGES')
  CONVERSION_TARGET_FORMAT: str = Field(..., alias='CONVERSION_TARGET_FORMAT')
  CONVERSION_SERVICE_URL: str = Field(..., alias='CONVERSION_SERVICE_URL')
  
  OCR_SERVICE_URL: str = Field(..., alias='OCR_SERVICE_URL')
  ANTIVIRUS_SERVICE_URL: str = Field(..., alias='ANTIVIRUS_SERVICE_URL')
  CONVERSION_SERVICE_URL: str = Field(..., alias='CONVERSION_SERVICE_URL')
  
  ALGORITHM: str = Field(..., alias='ALGORITHM')
  
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
      f'postgresql+psycopg2://{user}:{password}@'
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