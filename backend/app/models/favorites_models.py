from sqlalchemy import String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base


class FavoriteFolder(Base):
  __tablename__ = 'favorite_folders'
  __table_args__ = (
    UniqueConstraint(
      'user_id',
      'parent_folder_id',
      'folder_name',
      name='uq_favorite_folder_per_parent'
    ),
  )
  
  id:          Mapped[int]        = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:     Mapped[int]        = mapped_column(ForeignKey('users.id', ondelete='CASCADE')) # Владелец
  folder_name: Mapped[str]        = mapped_column(String(100)) # ! CHECK: длина Имя папки
  description: Mapped[str | None] = mapped_column(String(500)) # ! CHECK: длина
  parent_folder_id: Mapped[int | None] = mapped_column(ForeignKey('favorite_folders.id', ondelete='CASCADE'), nullable=True) # Рекурсивная ссылка
  created_at:  Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

  user          = relationship("User", back_populates="favorite_folders")
  parent_folder = relationship("FavoriteFolder", remote_side="FavoriteFolder.id", back_populates="child_folders")
  items         = relationship("FavoriteItem", back_populates="folder")
  child_folders = relationship("FavoriteFolder", back_populates="parent_folder")


class FavoriteItem(Base):
  __tablename__ = 'favorite_items'
  
  id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE')) # Документ
  folder_id:   Mapped[int] = mapped_column(ForeignKey('favorite_folders.id', ondelete='CASCADE')) # Папка

  document = relationship("Document",       back_populates="favorite_items")
  folder   = relationship("FavoriteFolder", back_populates="items")