from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config.settings import get_settings
from enum import enum

# Движок
engine = create_async_engine(
  get_settings().DATABASE_URL, 
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

class WorkflowEnum(str, enum.Enum): # `upload_requests`
  UPLOADED = 'uploaded'
  PROCESSING = 'processing'
  PENDING_REVIEW = 'pending_review'
  ACCEPTED = 'accepted'
  REJECTED = 'rejected'

class VisibilityEnum(str, enum.Enum): # `documents`
  PUBLISHED = 'published'
  UNLISTED = 'unlisted'
  ARCHIVED = 'archived'

class AccountEnum(str, enum.Enum): # `users`
  ACTIVE = 'active'
  BLOCKED = 'blocked'
  PENDING_REVIEW = 'pending_review'

class VerificationEnum(str, enum.Enum): # `users`
  UNVERIFIED = 'unverified'
  EMAIL_VERIFIED = 'email_verified'
  PHONE_VERIFIED = 'phone_verified'

class InvitationEnum(str, enum.Enum): # `group_invitations`
  PENDING = 'pending'
  ACCEPTED = 'accepted'
  EXPIRED = 'expired'
  REVOKED = 'revoked'

class DownloadTypeEnum(str, enum.Enum): # `history_downloads`
  PREVIEW = 'preview'
  FULL = 'full'
  EXPORT = 'export'

class ConversionEnum(str, enum.Enum):
  PENDING = 'pending'
  PROCESSING = 'processing'
  COMPLETED = 'completed'
  FAILED = 'failed'
  RETRYING = 'retrying'

class ReportTargetEnum(str, enum.Enum): # `reports`
  DOCUMENT = 'document'
  USER = 'user'
  GROUP = 'group'

class ReportCategoryEnum(str, enum.Enum): # `reports`
  COPYRIGHT = 'copyright'
  INAPPROPRIATE = 'inappropriate'
  VIRUS = 'virus'
  OTHER = 'other'

class ReportEnum(str, enum.Enum): # `reports`
  PENDING = 'pending'
  IN_REVIEW = 'in_review'
  RESOLVED = 'resolved'
  REJECTED = 'rejected'

class AuditTargetEnum(str, enum.Enum): # `audit_logs`
  DOCUMENT = 'document' 
  USER = 'user'
  GROUP = 'group'
  REPORT =  'report'

class NotificationChannelEnum(str, enum.Enum): # `notifications`
  IN_APP = 'in_app'
  EMAIL = 'email'

class NetworkEnum(str, enum.Enum): # `sync_states`
  SYNCED = 'synced'
  PENDING = 'pending'
  CONFLICT = 'conflict'
  DELETED_LOCALLY = 'deleted_locally'

class ConflictResolutionEnum(str, enum.Enum): # `sync_states`
  SERVER_WINS = 'server_wins'
  CLIENT_WINS = 'client_wins'
  MERGE = 'merge'