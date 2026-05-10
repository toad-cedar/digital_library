from sqlalchemy import String, mapped_column, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.config.database import Base


class FavoriteFolder(Base):
  __tablename__ = 'favorite_folders'
  
  id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:     Mapped[int] = mapped_column(ForeignKey('users.id')) # Владелец
  folder_name: Mapped[str] = mapped_column(String(100)) # ! CHECK: длина Имя папки
  description: Mapped[str | None] = mapped_column(String(500)) # CHECK: длина
  parent_folder_id: Mapped[int | None] = mapped_column(ForeignKey('favorite_folders.id')) # Рекурсивная ссылка
  created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

  user          = relationship("User", back_populates="favorite_folders")
  parent_folder = relationship("FavoriteFolder", remote_side=[id], back_populates="child_folders")
  items         = relationship("FavoriteItem", back_populates="folder")
  child_folders = relationship("FavoriteFolder", back_populates="parent_folder")


class FavoriteItem(Base):
  __tablename__ = 'favorite_item'
  
  id:          Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  document_id: Mapped[int] = mapped_column(ForeignKey('documents.id')) # Документ
  folder_id:   Mapped[int] = mapped_column(ForeignKey('favorite_folders.id')) # Папка

  document = relationship("Document", back_populates="favorite_items")
  folder   = relationship("FavoriteFolder", back_populates="items")