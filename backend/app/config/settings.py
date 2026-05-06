from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
from typing import List
import json

class Settings(BaseSettings):
  POSTGRES_HOST: str
  POSTGRES_PORT: int
  DATABASE_NAME: str
  POSTGRES_USER: str
  POSTGRES_PASSWORD: str
  
  @property
  def DATABASE_URL(self) -> str:
    return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.DATABASE_NAME}'
  # def DATABASE_URL(self) -> str:
  #   password = quote_plus(self.POSTGRES_PASSWORD)
  #   return (
  #     f"postgresql+asyncpg://"
  #     f"{self.POSTGRES_USER}:{password}@"
  #     f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/"
  #     f"{self.DATABASE_NAME}"
  #   )
  
  MINIO_ACCESS_KEY: str
  MINIO_SECRET_KEY: str
  MINIO_ENDPOINT: str
  MINIO_REGION: str = 'us-east-1'
  MINIO_SECURE: bool = False # Так как не используется https
  
  ELASTICSEARCH_HOST: str
  ELASTICSEARCH_PORT: int = 9200
  ELASTICSEARCH_PASSWORD: str
  
  SECRET_KEY: str # Секретный ключ для JWT
  ALGORITHM:  str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
  
  ALLOWED_ORIGINS: List[str]
  
  class Config:
    env_file = ".env"
    env_json_loads = json.loads

settings = Settings() # Глобальный экземпляр
