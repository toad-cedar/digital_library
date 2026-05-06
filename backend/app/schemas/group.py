from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GroupCreate(BaseModel):
  group_name: str


class GroupOut(BaseModel):
  id: int
  group_name: str
  creator_id: int

  class Config:
    from_attributes = True


class GroupMaterialCreate(BaseModel):
  group_id: int
  document_ids: List[int] # список ID документов
  message: Optional[str] = None


class GroupMaterialOut(BaseModel):
  id: int
  group_id: int
  sender_id: int
  message: Optional[str]
  sent_at: datetime
  document_ids: List[int]

  class Config:
    from_attributes = True