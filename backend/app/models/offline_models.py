from sqlalchemy import String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base


class OfflineFolder(Base):
  __tablename__ = 'offline_folders'
  __table_args__ = (
    UniqueConstraint(
      'user_id',
      'parent_folder_id',
      'folder_name',
      name='uq_favorite_folder_per_parent'
    ),
  )
  
  id:               Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:          Mapped[int] = mapped_column(ForeignKey('users.id'))
  folder_name:      Mapped[str] = mapped_column(String(100)) # ! CHECK: длина
  description:      Mapped[str | None] = mapped_column(String(500)) # ! CHECK: длина
  created_at:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  user          = relationship("User", back_populates="offline_folders")
  items         = relationship("OfflineItem", back_populates="folder")
  child_folders = relationship("OfflineFolder", back_populates="parent_folder")


class OfflineItem(Base):
  __tablename__ = 'offline_items'
  
  id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  document_id: Mapped[int] = mapped_column(ForeignKey('documents.id')) # Документ
  folder_id:   Mapped[int] = mapped_column(ForeignKey('offline_folders.id')) # Папка
  local_file_hash_checksum: Mapped[str] = mapped_column(String(64)) # Хеш локальной копии файла

  document = relationship("Document", back_populates="offline_items")
  folder   = relationship("OfflineFolder", back_populates="items")