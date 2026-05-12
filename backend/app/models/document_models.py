from sqlalchemy     import BigInteger, Text, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from datetime import datetime
from app.config.database import Base, VisibilityEnum, WorkflowEnum
from app.models.tag_models import documents_search_tags
from app.models.group_models import group_material_documents


class Document(Base):
  __tablename__ = 'documents'
  
  id:                 Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  title:              Mapped[str] = mapped_column(String(255), index=True) # ! CHECK: длина
  description:        Mapped[str | None] = mapped_column(Text) # Описание
  publish_date:       Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # Дата публикации # Как указать именно **timezone** datetime
  uploader_id:        Mapped[int] = mapped_column(ForeignKey('users.id')) # Автор загрузки
  moderator_id:       Mapped[int | None] = mapped_column(ForeignKey('users.id')) # Кто одобрил/отклонил последнюю версию
  minio_bucket:       Mapped[str] = mapped_column(String(100)) # Имя бакета. CHECK: длина имени бакета
  minio_object_path:  Mapped[str] = mapped_column(String(500))# Путь к объекту в MinIO
  file_original_name: Mapped[str | None] = mapped_column(String(255))# Исходное имя
  file_mime:          Mapped[str] = mapped_column(String(100)) # MIME-тип
  file_size:          Mapped[int] = mapped_column(BigInteger) # Размер в байтах
  file_hash:          Mapped[str] = mapped_column(String(64), unique=True, index=True) # ! SHA-256. CHECK: длина хеша
  format:             Mapped[str] = mapped_column(String(20)) # docx / pdf / pptx / txt
  converted_to_pdf:   Mapped[bool | None] = mapped_column(default=False)
  visibility_status:  Mapped[VisibilityEnum] = mapped_column(Enum(VisibilityEnum, name='visibility_enum', native_enum=True), default=VisibilityEnum.PUBLISHED) # VisibilityEnum (published / unlisted / archived)
  created_at:         Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  updated_at:         Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
  
  moderator        = relationship("User", foreign_keys=[moderator_id], back_populates="uploads_moderated")
  uploader         = relationship("User", foreign_keys=[uploader_id],  back_populates="documents_uploaded")
  tags             = relationship("SearchTag", secondary=documents_search_tags, back_populates="documents")
  view_history     = relationship("HistoryView",     back_populates="document")
  download_history = relationship("HistoryDownload", back_populates="document")
  history_versions = relationship("HistoryVersion",  back_populates="document")
  favorite_items   = relationship("FavoriteItem",    back_populates="document")
  offline_items    = relationship("OfflineItem",     back_populates="document")
  group_materials  = relationship("GroupMaterial", secondary=group_material_documents, back_populates="documents_attached") 
  conversion_jobs  = relationship("ConversionJob",   back_populates="target_document")


class UploadRequest(Base):
  __tablename__ = 'upload_requests'
  
  id:                   Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
  title:                Mapped[str] = mapped_column(String(255)) # ! CHECK: длина
  description:          Mapped[str | None] = mapped_column(Text) # Описание
  uploader_id:          Mapped[int]  = mapped_column(ForeignKey('users.id')) # Автор загрузки
  moderator_id:         Mapped[int | None] = mapped_column(ForeignKey('users.id')) # Проверяющий
  temporary_minio_path: Mapped[str] = mapped_column(String(500)) # Всегда в бакете `temporary`
  file_original_name:   Mapped[str | None] = mapped_column(String(255)) # Исходное имя
  file_mime:            Mapped[str] = mapped_column(String(100)) # MIME-тип
  file_size:            Mapped[int] = mapped_column(BigInteger) # Размер в байтах
  file_hash:            Mapped[str] = mapped_column(String(64), unique=True, index=True) # ! SHA-256. CHECK: длина хеша
  workflow_status:      Mapped[WorkflowEnum] = mapped_column(Enum(WorkflowEnum, name='workflow_enum', native_enum=True), default=WorkflowEnum.UPLOADED) # WorkflowEnum(uploaded / processing / pending_review / accepted / rejected)
  rejection_reason:     Mapped[str | None] = mapped_column(Text)
  processing_metadata:  Mapped[dict] = mapped_column(JSONB, server_default='{}')
  created_at:           Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

  user            = relationship("User", foreign_keys=[uploader_id],  back_populates="uploads_created")
  moderator       = relationship("User", foreign_keys=[moderator_id], back_populates="uploads_moderated")
  conversion_jobs = relationship("ConversionJob", back_populates="source_upload")
  moderation_assignments = relationship("ModerationAssignment", back_populates="upload_request")