from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from app.config.settings import get_settings
from enum import Enum

# Движок
engine = create_async_engine(
  get_settings().get_async_db_url, 
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

class WorkflowEnum(str, Enum): # `upload_requests`
  UPLOADED = 'uploaded'
  PROCESSING = 'processing'
  PENDING_REVIEW = 'pending_review'
  ACCEPTED = 'accepted'
  REJECTED = 'rejected'

class VisibilityEnum(str, Enum): # `documents`
  PUBLISHED = 'published'
  UNLISTED = 'unlisted'
  ARCHIVED = 'archived'

class AccountEnum(str, Enum): # `users`
  ACTIVE = 'active'
  BLOCKED = 'blocked'
  PENDING_REVIEW = 'pending_review'

class VerificationEnum(str, Enum): # `users`
  UNVERIFIED = 'unverified'
  EMAIL_VERIFIED = 'email_verified'
  PHONE_VERIFIED = 'phone_verified'

class InvitationEnum(str, Enum): # `group_invitations`
  PENDING = 'pending'
  ACCEPTED = 'accepted'
  EXPIRED = 'expired'
  REVOKED = 'revoked'

class DownloadTypeEnum(str, Enum): # `history_downloads`
  PREVIEW = 'preview'
  FULL = 'full'
  EXPORT = 'export'

class ConversionEnum(str, Enum):
  PENDING = 'pending'
  PROCESSING = 'processing'
  COMPLETED = 'completed'
  FAILED = 'failed'
  RETRYING = 'retrying'

class ReportTargetEnum(str, Enum): # `reports`
  DOCUMENT = 'document'
  USER = 'user'
  GROUP = 'group'

class ReportCategoryEnum(str, Enum): # `reports`
  COPYRIGHT = 'copyright'
  INAPPROPRIATE = 'inappropriate'
  VIRUS = 'virus'
  OTHER = 'other'

class ReportEnum(str, Enum): # `reports`
  PENDING = 'pending'
  IN_REVIEW = 'in_review'
  RESOLVED = 'resolved'
  REJECTED = 'rejected'

class AuditTargetEnum(str, Enum): # `audit_logs`
  DOCUMENT = 'document' 
  USER = 'user'
  GROUP = 'group'
  REPORT =  'report'

class NotificationChannelEnum(str, Enum): # `notifications`
  IN_APP = 'in_app'
  EMAIL = 'email'

class NetworkEnum(str, Enum): # `sync_states`
  SYNCED = 'synced'
  PENDING = 'pending'
  CONFLICT = 'conflict'
  DELETED_LOCALLY = 'deleted_locally'

class ConflictResolutionEnum(str, Enum): # `sync_states`
  SERVER_WINS = 'server_wins'
  CLIENT_WINS = 'client_wins'
  MERGE = 'merge'