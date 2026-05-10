from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import settings
import enum

# Движок
engine = create_async_engine(
  settings.DATABASE_URL, 
  pool_pre_ping=True, # Проверка соединения
  echo=False # Откл. вывод SQL-запросов в консось
)

# Создание сессии 
async_session_maker = async_sessionmaker(engine, expire_on_commit=False) 

class Base(AsyncAttrs, DeclarativeBase):
  __abstract__ = True
  

async def get_db_session():
  async with async_session_maker() as session:
    yield session 

class WorkflowEnum(str, enum.Enum):
  UPLOADED = 'uploaded'
  PROCESSING = 'processing'
  PENDING_REVIEW = 'pending_review'
  ACCEPTED = 'accepted'
  REJECTED = 'rejected'

class VisibilityEnum(str, enum.Enum):
  PUBLISHED = 'published'
  UNLISTED = 'unlisted'
  ARCHIVED = 'archived'

class AccountEnum(str, enum.Enum):
  ACTIVE = 'active'
  BLOCKED = 'blocked'
  PENDING_REVIEW = 'pending_review'

class VerificationEnum(str, enum.Enum):
  UNVERIFIED = 'unverified'
  EMAIL_VERIFIED = 'email_verified'
  PHONE_VERIFIED = 'phone_verified'