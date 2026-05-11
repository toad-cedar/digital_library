from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class FavoriteFolderCreate(BaseModel):
  folder_name: str = Field(min_length=1, max_length=100)
  description: str | None = Field(None, max_length=500)
  parent_folder_id: int | None = None


class FavoriteFolderRead(BaseModel):
  id: int
  folder_name: str
  description: str | None
  parent_folder_id: int | None
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)


class FavoriteFolderUpdate(BaseModel):
  folder_name: str | None = Field(None, min_length=1, max_length=100)
  description: str | None = Field(None, max_length=500)
  parent_folder_id: int | None = None


class FavoriteItemAdd(BaseModel):
  document_id: int


class FavoriteItemRemove(BaseModel):
  document_id: int
  folder_id: int