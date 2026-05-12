from sqlalchemy     import String, Enum, DateTime, ForeignKey, Uuid, func, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, INET

from app.config.database import Base, AuditTargetEnum, NotificationChannelEnum, ConflictResolutionEnum, NetworkEnum
from datetime import datetime
from uuid import UUID


class AuditLog(Base):
  __tablename__ = 'audit_logs'
  
  id:          Mapped[int]  = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:     Mapped[int]  = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True)
  action:      Mapped[str]  = mapped_column(String(50)) # upload / delete / approve / reject
  target_uuid: Mapped[UUID] = mapped_column(Uuid(as_uuid=True)) # ID целевого объекта
  target_type: Mapped[AuditTargetEnum] = mapped_column(Enum(AuditTargetEnum, name='audit_enum', native_enum=True)) # AuditTargetEnum(document / user / group)
  details:     Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
  ip_address:  Mapped[str | None] = mapped_column(INET)
  success:     Mapped[bool]
  created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  user = relationship("User", back_populates="audit_logs")


class Notification(Base):
  __tablename__ = 'notifications'
  
  id:          Mapped[int]  = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:     Mapped[int]  = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
  source_type: Mapped[str]  = mapped_column(String(50)) # document / upload_requests / group / report / system
  source_id:   Mapped[int]  # Номер строки сущности source_type
  event_type:  Mapped[str]  = mapped_column(String(50)) # approved / rejected / invited / new_material / sync_conflict / password_reset
  title:       Mapped[str]  = mapped_column(String(255)) # Заголовок
  content:     Mapped[dict] = mapped_column(JSONB)
  channel:     Mapped[NotificationChannelEnum] = mapped_column(Enum(NotificationChannelEnum, name='notification_channel_enum', native_enum=True)) # NotificationChannelEnum(in_app, email)
  is_read:     Mapped[bool] = mapped_column(default=False)
  read_at:     Mapped[datetime | None] = mapped_column(DateTime()) # Время прочтения
  created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  expires_at:  Mapped[datetime] = mapped_column(DateTime()) # Срок жизни уведомления
  
  user = relationship("User", back_populates="notifications")


class RegistryDevice(Base):
  __tablename__ = 'registry_devices'

  id:          Mapped[int]  = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:     Mapped[int]  = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True) # Владелец
  device_uuid: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), unique=True) # Генерация при первом запуске клиента
  device_name: Mapped[str]  = mapped_column(String(100)) # Имя устройства/пользователя
  platform:    Mapped[str]  = mapped_column(String(20)) # ОС/платформа
  app_version: Mapped[str]  = mapped_column(String(20)) # Семантическое версионирование
  last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime()) # Для отключения неактивных сессий
  is_active:   Mapped[bool] = mapped_column(default=True) # Статус активности
  created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  user        = relationship("User", back_populates="registered_devices")
  sync_states = relationship("SyncState", back_populates="device")

class SyncState(Base):
  __tablename__ = 'sync_states'
  
  id:              Mapped[int]  = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:         Mapped[int]  = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True) # Владелец
  device_id:       Mapped[int]  = mapped_column(ForeignKey('registry_devices.id', ondelete='CASCADE'), index=True) # Устройство
  entity_type:     Mapped[str]  = mapped_column(String(20)) # document / folder / tag
  entity_id:       Mapped[UUID] = mapped_column(Uuid(as_uuid=True)) # ID сущности
  local_checksum:  Mapped[str]  = mapped_column(String(64)) # SHA-256 локального файла
  server_checksum: Mapped[str]  = mapped_column(String(64)) # SHA-256 серверного файла
  last_sync_at:    Mapped[datetime] = mapped_column(DateTime()) # Время последней синхронизации
  network_status:  Mapped[NetworkEnum] = mapped_column(Enum(NetworkEnum, name='network_enum', native_enum=True), default=NetworkEnum.SYNCED) # NetworkEnum(synced / pending / conflict)
  conflict_resolution: Mapped[ConflictResolutionEnum | None] = mapped_column(Enum(ConflictResolutionEnum, name='conflict_resolution_enum', native_enum=True)) # ConflictResolutionEnum(server_wins / client_wins / merge)
  
  user   = relationship("User", back_populates="sync_states")
  device = relationship("RegistryDevice", back_populates="sync_states")
