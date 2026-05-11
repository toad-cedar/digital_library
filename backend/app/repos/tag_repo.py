from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from app.models.tag_models import SearchTag, documents_search_tags
from app.repos.base_repo import GenericRepository


class TagRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.base = GenericRepository(db_session, SearchTag)

  async def get_by_id(self, tag_id: int) -> Optional[SearchTag]:
    return await self.base.get_by_id(tag_id)

  async def get_or_create_by_name(self, tag_name: str) -> SearchTag:
    stmt = select(SearchTag).where(SearchTag.tag_name == tag_name)
    tag = (await self.db.execute(stmt)).scalar_one_or_none()
    if not tag:
      tag = SearchTag(tag_name=tag_name)
      self.db.add(tag)
      await self.db.flush()
    return tag

  async def get_by_document(self, document_id: int) -> List[SearchTag]:
    stmt = select(SearchTag).join(documents_search_tags).where(documents_search_tags.c.document_id == document_id)
    return (await self.db.execute(stmt)).scalars().all()

  async def link_document(self, document_id: int, tag_ids: List[int]) -> None:
    if not tag_ids:
      return
    values = [{"document_id": document_id, "tag_id": tid} for tid in tag_ids]
    stmt = insert(documents_search_tags).values(values)
    await self.db.execute(stmt)

  async def unlink_document(self, document_id: int, tag_ids: Optional[List[int]] = None) -> None:
    stmt = delete(documents_search_tags).where(documents_search_tags.c.document_id == document_id)
    if tag_ids:
      stmt = stmt.where(documents_search_tags.c.tag_id.in_(tag_ids))
    await self.db.execute(stmt)