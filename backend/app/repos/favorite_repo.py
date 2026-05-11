from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from app.models.favorites_models import FavoriteFolder, FavoriteItem
from app.repos.base_repo import GenericRepository


class FavoriteRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.folders = GenericRepository(db_session, FavoriteFolder)
    self.items = GenericRepository(db_session, FavoriteItem)

  async def get_folder_by_id(self, folder_id: int) -> Optional[FavoriteFolder]:
    return await self.folders.get_by_id(folder_id)

  async def get_user_folders(self, user_id: int, offset: int = 0, limit: int = 10) -> Tuple[List[FavoriteFolder], int]:
    base = select(FavoriteFolder).where(FavoriteFolder.user_id == user_id)
    count = (await self.db.execute(select(func.count(FavoriteFolder.id)).where(FavoriteFolder.user_id == user_id))).scalar() or 0
    items = (await self.db.execute(base.offset(offset).limit(limit))).scalars().all()
    return items, count

  async def create_folder(self, folder: FavoriteFolder) -> FavoriteFolder:
    return await self.folders.create(folder)

  async def delete_folder(self, folder_id: int) -> bool:
    return await self.folders.delete(folder_id)

  async def add_item(self, item: FavoriteItem) -> FavoriteItem:
    return await self.items.create(item)

  async def get_item(self, document_id: int, folder_id: int) -> Optional[FavoriteItem]:
    stmt = select(FavoriteItem).where(FavoriteItem.document_id == document_id, FavoriteItem.folder_id == folder_id)
    return (await self.db.execute(stmt)).scalar_one_or_none()

  async def delete_item(self, document_id: int, folder_id: int) -> bool:
    stmt = delete(FavoriteItem).where(FavoriteItem.document_id == document_id, FavoriteItem.folder_id == folder_id)
    return (await self.db.execute(stmt)).rowcount > 0