from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class GroupCreate(BaseModel):
  group_name: str = Field(min_length=2, max_length=100)

class GroupRead(BaseModel):
  id: int
  group_name: str
  creator_id: int
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)

class GroupUpdate(BaseModel):
  group_name: Optional[str] = Field(None, min_length=2, max_length=100)

class MemberAddRequest(BaseModel):
  user_id: int

class InviteRequest(BaseModel):
  invited_email: EmailStr

class InviteAcceptRequest(BaseModel):
  token: str

class GroupMaterialRead(BaseModel):
  id: int
  group_id: int
  sender_id: int
  sent_at: datetime
  document_ids: List[int]
  model_config = ConfigDict(from_attributes=True)

class GroupMaterialCreate(BaseModel):
  document_ids: list[int]
  message: Optional[str] = None
