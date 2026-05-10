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
    CheckConstraint('failed_login_attempts >= 0'),
  )
  id:                  Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  username:            Mapped[str] = mapped_column(String(50), unique=True) # ! CHECK: длина, формат
  email:               Mapped[str] = mapped_column(String(255), unique=True) # ! CHECK: формат 
  password_hash:       Mapped[str] = mapped_column(String(255)) # ! CHECK: длина
  mfa_secret:          Mapped[str | None] # Зашифрован, NULL если отключено
  mfa_enabled:         Mapped[bool] = mapped_column(default=False)
  last_login_at:       Mapped[datetime | None] # Время последнего входа
  upload_quota_used:   Mapped[int]  = mapped_column(default=0) # Байты за текущие сутки
  verification_status: Mapped[VerificationEnum] = mapped_column(Enum(VerificationEnum, native_enum=True), default=VerificationEnum.UNVERIFIED) # VerificationEnum(unverified / email_verified / phone_verified)
  account_status:      Mapped[AccountEnum] = mapped_column(Enum(AccountEnum, native_enum=True), default=AccountEnum.ACTIVE) # AccountEnum(active / blocked / pending_review)
  failed_login_attempts: Mapped[int] = mapped_column(default=0) # Cброс при успехе 
  registration_date:   Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  created_at:          Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at:          Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

  role               = relationship("Role", back_populates="users")
  uploads_created    = relationship("UploadRequest", foreign_keys="UploadRequest.uploader_id", back_populates="user")
  uploads_moderated  = relationship("UploadRequest", foreign_keys="UploadRequest.moderator_id", back_populates="moderator")
  documents_uploaded = relationship("Document", back_populates="uploader")
  groups_created     = relationship("Group", back_populates="creator")
  history            = relationship("ViewHistory", back_populates="user")
  favorite_folders   = relationship("FavoriteFolder", back_populates="user")
  offline_folders    = relationship("OfflineFolder", back_populates="user")
  group_materials_sent = relationship("GroupMaterial", back_populates="sender")
  groups_joined      = relationship("Group", secondary=groups_users, back_populates="members")


class Role(Base):
  __tablename__ = 'roles'
  
  id:        Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  role_name: Mapped[str] = mapped_column(String(30), unique=True) # user / teacher / moderator / admin
  
  users       = relationship("User",       back_populates="role")
  permissions = relationship("Permission", secondary=roles_permissions, back_populates="roles")


class Permission(Base):
  __tablename__ = 'permissions'
  
  id:              Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  permission_name: Mapped[str] = mapped_column(String(100), unique=True)
  
  roles = relationship("Role", secondary=roles_permissions, back_populates="permissions")