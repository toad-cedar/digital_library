from sqlalchemy import String, Column, Integer, DateTime, ForeignKey, Table, Enum, func, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base, VerificationEnum, AccountEnum
from app.models.group_models import groups_users


roles_permissions = Table(
  'roles_permissions', Base.metadata,
  Column('role_id',       Integer, ForeignKey('roles.id'),       primary_key=True),
  Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

class User(Base):
  __tablename__ = 'users'
  __table_args__ = (
    CheckConstraint(
      'failed_login_attempts >= 0',
      name='ck_users_failed_login_attempts_positive'
    ),
  )
  id:                  Mapped[int]        = mapped_column(primary_key=True, autoincrement=True, index=True)
  username:            Mapped[str]        = mapped_column(String(50), unique=True) # ! CHECK: длина, формат
  email:               Mapped[str]        = mapped_column(String(255), unique=True) # ! CHECK: формат 
  password_hash:       Mapped[str]        = mapped_column(String(255)) # ! CHECK: длина
  mfa_secret:          Mapped[str | None] = mapped_column(String(255)) # Зашифрован, NULL если отключено
  mfa_enabled:         Mapped[bool]       = mapped_column(default=False)
  last_login_at:       Mapped[datetime | None] = mapped_column(DateTime(timezone=True))# Время последнего входа
  upload_quota_used:   Mapped[int]        = mapped_column(default=0) # Байты за текущие сутки
  verification_status: Mapped[VerificationEnum] = mapped_column(Enum(VerificationEnum, name='verification_enum',  native_enum=True), default=VerificationEnum.UNVERIFIED) # VerificationEnum(unverified / email_verified / phone_verified)
  account_status:      Mapped[AccountEnum] = mapped_column(Enum(AccountEnum, name='account_enum', native_enum=True), default=AccountEnum.ACTIVE) # AccountEnum(active / blocked / pending_review)
  failed_login_attempts: Mapped[int]      = mapped_column(default=0) # Cброс при успехе 
  registration_date:   Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
  created_at:          Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at:          Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
  role_id:             Mapped[int | None]        = mapped_column(ForeignKey('roles.id')) 

  role                 = relationship("Role",            back_populates="users")
  uploads_created      = relationship("UploadRequest", foreign_keys="UploadRequest.uploader_id", back_populates="user")
  documents_uploaded   = relationship("Document",        back_populates="uploader")
  versions_uploaded    = relationship("HistoryVersion",  foreign_keys="HistoryVersion.uploaded_by", back_populates="uploader")
  invitations_created  = relationship("GroupInvitation", foreign_keys="GroupInvitation.created_by", back_populates="creator") 
  versions_uploaded    = relationship("HistoryVersion",  foreign_keys="HistoryVersion.uploaded_by", back_populates="uploader")
  view_history         = relationship("HistoryView",     back_populates="user")
  download_history     = relationship("HistoryDownload", back_populates="user")
  favorite_folders     = relationship("FavoriteFolder",  back_populates="user")
  offline_folders      = relationship("OfflineFolder",   back_populates="user")
  group_materials_sent = relationship("GroupMaterial",   back_populates="sender")
  groups_joined        = relationship("Group",  secondary=groups_users, back_populates="members")
  reports_made         = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
  reports_resolved     = relationship("Report", foreign_keys="Report.resolved_by", back_populates="resolver")
  uploads_moderated    = relationship("UploadRequest", foreign_keys="UploadRequest.moderator_id", back_populates="moderator")
  moderation_tasks     = relationship("ModerationAssignment", back_populates="moderator")
  audit_logs           = relationship("AuditLog",        back_populates="user")
  notifications        = relationship("Notification",    back_populates="user")
  registered_devices   = relationship("RegistryDevice",  back_populates="user")
  sync_states          = relationship("SyncState",       back_populates="user")


class Role(Base):
  __tablename__ = 'roles'
  
  id:        Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  role_name: Mapped[str] = mapped_column(String(30), unique=True) # user / teacher / moderator / admin
  
  users       = relationship("User", back_populates="role")
  permissions = relationship("Permission", secondary=roles_permissions, back_populates="roles")


class Permission(Base):
  __tablename__ = 'permissions'
  
  id:              Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  permission_name: Mapped[str] = mapped_column(String(100), unique=True)
  
  roles = relationship("Role", secondary=roles_permissions, back_populates="permissions")