from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from app.models.document_models import Document
from app.config.database import VisibilityEnum
from app.repos.base_repo import GenericRepository


class DocumentRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.base = GenericRepository(db_session, Document)

  async def get_by_id(self, document_id: int) -> Optional[Document]:
    stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .options(selectinload(Document.tags))
      .where(Document.id == document_id)
    )
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_by_ids(self, document_ids: List[int]) -> List[Document]:
    if not document_ids:
      return []
    stmt = (
      select(Document)
      .options(selectinload(Document.uploader))
      .where(Document.id.in_(document_ids))
    )
    return (await self.db_session.execute(stmt)).scalars().all()

  async def get_by_hash(self, file_hash: str) -> Optional[Document]:
    stmt = select(Document).where(Document.file_hash == file_hash)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_all(
    self,
    visibility: Optional[VisibilityEnum] = None,
    format_filter: Optional[str] = None,
    offset: int = 0,
    limit: int = 10
  ) -> Tuple[List[Document], int]:
    stmt = select(Document).options(selectinload(Document.uploader))
    count_stmt = select(func.count(Document.id))

    if visibility is not None:
      stmt = stmt.where(Document.visibility_status == visibility)
      count_stmt = count_stmt.where(Document.visibility_status == visibility)
    if format_filter is not None:
      stmt = stmt.where(Document.format == format_filter)
      count_stmt = count_stmt.where(Document.format == format_filter)

    total = (await self.db_session.execute(count_stmt)).scalar() or 0
    docs = (await self.db_session.execute(
      stmt.order_by(Document.publish_date.desc()).offset(offset).limit(limit)
    )).scalars().all()
    return docs, total

  async def get_and_lock(self, document_id: int) -> Optional[Document]:
    """Получает `Document` и устанавливает блокировку строки (SELECT ... FOR UPDATE)."""
    stmt = select(Document).where(Document.id == document_id).with_for_update()
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def update_visibility(self, document_id: int, status: VisibilityEnum) -> Optional[Document]:
    stmt = update(Document).where(Document.id == document_id).values(visibility_status=status).returning(Document)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def create(self, document: Document) -> Document:
    return await self.base.create(document)

  async def update(self, document_id: int, data: dict) -> Optional[Document]:
    return await self.base.update(document_id, data)

  async def delete(self, document_id: int) -> bool:
    return await self.base.delete(document_id)