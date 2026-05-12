from sqlalchemy     import Text, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import INET
from datetime import datetime
from app.config.database import Base, DownloadTypeEnum


class HistoryView(Base):
  __tablename__ = 'history_views'
  
  id:          Mapped[int]  = mapped_column(primary_key=True, autoincrement=True, index=True) 
  user_id:     Mapped[int]  = mapped_column(ForeignKey('users.id',    ondelete='CASCADE')) # Пользователь
  document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE')) # Документ
  viewed_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # Время просмотра
  
  user     = relationship("User",     back_populates="view_history")
  document = relationship("Document", back_populates="view_history")


class HistoryDownload(Base):
  __tablename__ = 'history_downloads'
  
  id:            Mapped[int]        = mapped_column(primary_key=True, autoincrement=True, index=True)
  user_id:       Mapped[int | None] = mapped_column(ForeignKey('users.id',     ondelete='SET NULL')) # NULL для гостей/анонимов
  document_id:   Mapped[int]        = mapped_column(ForeignKey('documents.id', ondelete='CASCADE')) # Документ
  downloaded_at: Mapped[datetime]   = mapped_column(DateTime(timezone=True), index=True) # Время скачивания
  ip_address:    Mapped[str | None] = mapped_column(INET) # Для аудита и rate-limit
  user_agent:    Mapped[str | None] = mapped_column(Text) # Клиентский заголовок
  download_type: Mapped[DownloadTypeEnum] = mapped_column(Enum(DownloadTypeEnum, name='download_enum', native_enum=True), default=DownloadTypeEnum.PREVIEW) # DownloadTypeEnum(preview / full / export)
  is_success:    Mapped[bool]       = mapped_column(default=False) # Статус presigned URL
  
  user     = relationship("User",     back_populates="download_history")
  document = relationship("Document", back_populates="download_history")