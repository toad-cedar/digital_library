from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repos.upload_repo import UploadRequestRepository
from app.repos.document_repo import DocumentRepository
from app.repos.status_repo import StatusRepository
from app.services.minio_service import MinioService
from app.services.search_service import SearchService
from app.models.orm_models import User, Document
from app.schemas import UploadRequestCreate
from app.schemas import DocumentCreate
from PIL import Image # Pillow: работа с изображениями

import fitz # PyMuPDF
import hashlib
import logging

logger = logging.getLogger(__name__)


class UploadService:
  def __init__(
    self,
    db_session: AsyncSession,
    minio_service: MinioService,
    search_service: SearchService,
    status_repo: StatusRepository
  ):
    self.db_session = db_session
    self.upload_repo = UploadRequestRepository(db_session)
    self.document_repo = DocumentRepository(db_session)
    self.minio_service = minio_service
    self.search_service = search_service
    self.status_repo = status_repo  

  async def process_upload(
    self,
    file_bytes: bytes,
    original_filename: str,
    user: User,
    bucket_name: str = "uploads",
    document_title: Optional[str] = None,
    document_description: Optional[str] = None,
    document_author: Optional[str] = None,
    tags: list[str] = [],
  ) -> dict:
    """
    Основной метод для обработки загрузки файла.
    1. Вычисляет хеш файла.
    2. Проверяет дубликат по хешу.
    3. Загружает файл в MinIO.
    4. Генерирует и загружает обложку в MinIO (если PDF)
    5. Создает запись в БД (в таблице documents, статус 'одобрен').
    6. Индексирует документ в Elasticsearch.
    """
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    file_size = len(file_bytes)

    # 1. Проверка на дубликат
    existing_doc = await self.document_repo.get_by_hash(file_hash)
    if existing_doc:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Document with this hash already exists (ID: {existing_doc.id}).",
      )

    # 2. Загрузка в MinIO
    object_name = f"{user.id}/{file_hash}/{original_filename}"
    try:
      await self.minio_service.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=file_bytes,
        length=file_size,
      )
    except Exception as e:
      logger.error(f"Failed to upload file to MinIO: {e}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to store file in storage.",
      )
    
    cover_object_name = None # Путь к обложке в MinIO
    cover_bucket_name = "covers" # Имя бакета для обложек
    if original_filename.lower().endswith('.pdf'):
      try:
        # 1. Открыть PDF из bytes
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        # 2. Получить первую страницу
        first_page = pdf_document[0]
        # 3. Рендерить страницу в изображение (например, PNG)
        #    Можно настроить разрешение (dpi) для уменьшения размера
        #    72 DPI дает относительно низкое разрешение, подходит для обложки
        dpi = 72
        mat = fitz.Matrix(dpi / 72, dpi / 72) # 72 это базовое разрешение MuPDF
        pix = first_page.get_pixmap(matrix=mat)
        cover_image_bytes = pix.tobytes("png")

        # 4. Подготовить имя объекта для обложки
        cover_object_name = f"{user.id}/{file_hash}/cover.png"

        # 5. Загрузить обложку в MinIO
        await self.minio_service.put_object(
          bucket_name=cover_bucket_name, # Обложки можно хранить в том же бакете или в отдельном
          object_name=cover_object_name,
          data=cover_image_bytes,
          length=len(cover_image_bytes),
          content_type="image/png"
        )
        logger.info(f"Cover generated and uploaded for {original_filename} -> {cover_object_name}")

      except Exception as e:
        logger.error(f"Failed to generate or upload cover for {original_filename}: {e}")
        cover_object_name = None
        cover_bucket_name = None
    
    # автоматические одобрение
    approved_status_id = await self.status_repo.get_status_id_by_name("approved")
    if not approved_status_id:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Status 'approved' not found in database"
    )

    # 3. Создание записи в БД
    # Предполагаем, что формат определяется по расширению filename или берется из параметра
    format_name = "unknown"
    if original_filename.lower().endswith('.pdf'):
      format_name = "pdf"
    elif original_filename.lower().endswith('.docx'):
      format_name = "docx"
    elif original_filename.lower().endswith('.doc'):
      format_name = "doc"
    elif original_filename.lower().endswith('.txt'):
      format_name = "txt"
    elif original_filename.lower().endswith('.md'):
      format_name = "md"

    format_obj = await self.document_repo.get_or_create_format(name=format_name)

    doc_data = DocumentCreate(
      title=document_title or original_filename,
      description=document_description,
      author=document_author,
      tag_names=tags,
    )

    new_doc = Document(
      title=doc_data.title,
      description=doc_data.description,
      author=doc_data.author,
      uploader_id=user.id,
      format_id=format_obj.id,
      minio_bucket=bucket_name,
      minio_object_path=object_name,
      cover_bucket=cover_bucket_name,
      cover_url=cover_object_name,
      file_original_name=original_filename,
      file_size=file_size,
      file_hash=file_hash,
      status_id=approved_status_id,  # В мин. версии сразу одобряем
      converted_to_pdf=original_filename.lower().endswith('.pdf')      
      # publish_date и upload_date заполнятся автоматически
    )
    
    # Сохраняем документ
    created_doc = await self.document_repo.create(new_doc)

    await self.db_session.flush()

    # Привязываем теги
    tag_objects = await self.document_repo.get_or_create_tags(doc_data.tag_names)

    from sqlalchemy import insert
    from app.models.orm_models import documents_search_tags # Импортируем вспомогательную таблицу

    if tag_objects: # Если есть теги для привязки
      # Подготовим список словарей для вставки
      tag_links_to_add = [
          {"document_id": created_doc.id, "tag_id": tag_obj.id}
          for tag_obj in tag_objects
      ]
      # Выполним вставку через Core API
      stmt = insert(documents_search_tags).values(tag_links_to_add)
      await self.db_session.execute(stmt)

    await self.db_session.commit()
    await self.db_session.refresh(created_doc)

    # 4. Индексация в Elasticsearch
    # Список имён тегов для индексации
    tag_names_for_indexing = [tag_obj.tag_name for tag_obj in tag_objects]
    try:
      # Передаётся tag_names в index_document
      await self.search_service.index_document(created_doc, tag_names=tag_names_for_indexing)
    except Exception as e:
      logger.warning(f"Failed to index document {created_doc.id} in Elasticsearch: {e}")
      # Не вызывается HTTPException, так как документ уже сохранен в БД и MinIO.

    return {
      "message": "File processed and stored successfully.",
      "document_id": created_doc.id,
      "title": created_doc.title,
    }
    
