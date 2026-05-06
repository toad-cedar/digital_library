from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from app.models.orm_models import Document, DocumentTag, SupportedFormat, User, UploadStatus


class DocumentRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session

  async def get_by_id(self, document_id: int) -> Optional[Document]:
    """Получает документ по ID с предзагрузкой связанных объектов."""
    stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .options(selectinload(Document.format_obj))
      .options(selectinload(Document.tags))
      .options(selectinload(Document.status_obj))
      .where(Document.id == document_id)
    )
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_by_ids(self, document_ids: List[int]) -> List[Document]:
    """Получает список документов по списку ID с предзагрузкой связанных объектов."""
    if not document_ids:
      return []
    stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .options(selectinload(Document.format_obj))
      .options(selectinload(Document.tags))
      .options(selectinload(Document.status_obj))
      .where(Document.id.in_(document_ids))
    )
    result = await self.db_session.execute(stmt)
    return result.scalars().all()

  async def get_by_hash(self, file_hash: str) -> Optional[Document]:
    """Проверяет наличие документа с таким же хешем."""
    stmt = (
      select(Document)
      .options(selectinload(Document.uploader)) # Предзагрузка uploader
      .options(selectinload(Document.format_obj)) # Предзагрузка format_obj
      .options(selectinload(Document.tags)) # Предзагрузка tags
      .options(selectinload(Document.status_obj))
      .where(Document.file_hash == file_hash)
    )
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_all(
    self, offset: int = 0, limit: int = 10, status: Optional[int] = None
  ) -> Tuple[List[Document], int]: # Возвращает список и общее количество
    """Получает список документов с пагинацией и опциональным фильтром по статусу."""
    count_stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .options(selectinload(Document.format_obj)) 
      .options(selectinload(Document.tags))
      .options(selectinload(Document.status_obj))
    )
    if status is not None:
      count_stmt = count_stmt.where(Document.status_id == status)
      
    total_count_result = await self.db_session.execute(select(func.count()).select_from(count_stmt.subquery()))
    total_count = total_count_result.scalar()

    stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .options(selectinload(Document.format_obj))
      .options(selectinload(Document.tags))
      .options(selectinload(Document.status_obj))
    )
    if status is not None:
      stmt = stmt.where(Document.status_id == status) # Только если status не None
    else:
      # Если status None, фильтр не добавляется, выбираются все статусы
      pass

    stmt = stmt.offset(offset).limit(limit)
    
    result = await self.db_session.execute(stmt)
    documents = result.scalars().all()
    return documents, total_count

  async def create(self, document: Document) -> Document:
    """Создаёт новый документ."""
    self.db_session.add(document)
    await self.db_session.flush() # Получаем ID без коммита всей транзакции
    return document

  async def update(self, document_id: int, update_data: dict) -> Optional[Document]:
    """Обновляет документ по ID."""
    stmt = (
      update(Document)
      .where(Document.id == document_id)
      .values(**update_data)
      .returning(Document)
    )
    result = await self.db_session.execute(stmt)
    updated_doc = result.scalar_one_or_none()
    if updated_doc:
      await self.db_session.commit()
      # Не забываем перезагрузить связанные объекты, если они изменились
      await self.db_session.refresh(updated_doc)
    else:
      await self.db_session.rollback()
    return updated_doc

  async def delete(self, document_id: int) -> bool:
    """Удаляет документ по ID."""
    stmt = delete(Document).where(Document.id == document_id)
    result = await self.db_session.execute(stmt)
    if result.rowcount > 0:
      await self.db_session.commit()
      return True
    else:
      await self.db_session.rollback()
      return False

  async def get_or_create_format(self, name: str) -> SupportedFormat:
    """Получает формат по имени или создаёт новый, если не существует."""
    stmt = select(SupportedFormat).where(SupportedFormat.format_name == name)
    result = await self.db_session.execute(stmt)
    format_obj = result.scalar_one_or_none()
    if not format_obj:
      format_obj = SupportedFormat(format_name=name)
      self.db_session.add(format_obj)
      await self.db_session.flush() # Получаем ID
    return format_obj

  async def get_or_create_tags(self, tag_names: List[str]) -> List[DocumentTag]:
    """Получает список тегов по именам или создаёт новые, если не существуют."""
    if not tag_names:
      return []
    # Получаем существующие
    existing_tags_stmt = select(DocumentTag).where(DocumentTag.tag_name.in_(tag_names))
    existing_tags_result = await self.db_session.execute(existing_tags_stmt)
    existing_tags = existing_tags_result.scalars().all()
    existing_tag_names = {tag.tag_name for tag in existing_tags}

    # Находим теги, которых нет в БД
    missing_tag_names = set(tag_names) - existing_tag_names

    # Создаём недостающие
    new_tags = []
    if missing_tag_names:
      for name in missing_tag_names:
        new_tag = DocumentTag(tag_name=name)
        self.db_session.add(new_tag)
        new_tags.append(new_tag)
      await self.db_session.flush() # Получаем ID новых тегов

    return existing_tags + new_tags
