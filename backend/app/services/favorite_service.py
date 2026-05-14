from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.favorite_repo import FavoriteRepository
from app.schemas.favorites import (
  FavoriteFolderCreate, FavoriteFolderRead, FavoriteFolderUpdate,
  FavoriteItemAdd, FavoriteItemRemove
)
from app.schemas.common import PaginationResponse
from app.models.favorites_models import FavoriteFolder, FavoriteItem


class FavoriteService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.fav_repo = FavoriteRepository(db_session)

  async def get_folders(self, user_id: int, page: int, page_size: int) -> PaginationResponse[FavoriteFolderRead]:
    offset = (page - 1) * page_size
    folders, total = await self.fav_repo.get_user_folders(user_id, offset, page_size)
    items = [FavoriteFolderRead.model_validate(f) for f in folders]
    return PaginationResponse(data=items, total=total, page=page, page_size=page_size)

  async def create_folder(self, user_id: int, data: FavoriteFolderCreate) -> FavoriteFolderRead:
    folder = FavoriteFolder(
      user_id=user_id, 
      folder_name=data.folder_name, 
      description=data.description, 
      parent_folder_id=data.parent_folder_id,
    )
    created = await self.fav_repo.create_folder(folder)
    await self.db_session.commit()
    return FavoriteFolderRead.model_validate(created)

  async def update_folder(self, user_id: int, folder_id: int, data: FavoriteFolderUpdate) -> FavoriteFolderRead:
    folder = await self.fav_repo.get_folder_by_id(folder_id)
    if not folder or folder.user_id != user_id:
      raise ValueError("Folder not found or access denied")
        
    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
      return FavoriteFolderRead.model_validate(folder)
        
    updated = await self.fav_repo.folders.update(folder_id, update_data)
    await self.db_session.commit()
    return FavoriteFolderRead.model_validate(updated)

  async def add_item(self, user_id: int, folder_id: int, data: FavoriteItemAdd) -> bool:
    folder = await self.fav_repo.get_folder_by_id(folder_id)
    if not folder or folder.user_id != user_id:
      raise ValueError("Folder not found or access denied")
        
    if await self.fav_repo.get_item(data.document_id, folder_id):
      return True
        
    item = FavoriteItem(document_id=data.document_id, folder_id=folder_id)
    await self.fav_repo.add_item(item)
    await self.db_session.commit()
    return True

  async def remove_item(self, user_id: int, folder_id: int, data: FavoriteItemRemove) -> bool:
    folder = await self.fav_repo.get_folder_by_id(folder_id)
    if not folder or folder.user_id != user_id:
      raise ValueError("Folder not found or access denied")
    
    success = await self.fav_repo.delete_item(data.document_id, folder_id)
    await self.db_session.commit()
    return success