from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserShort(BaseModel):
  id: int
  username: str
  model_config = ConfigDict(from_attributes=True)

class UserRead(BaseModel):
  id: int
  username: str
  email: EmailStr
  account_status: str
  verification_status: str
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
  username: Optional[str] = Field(None, min_length=3, max_length=100)
  email: Optional[EmailStr] = None

class UserProfileRead(BaseModel):
  role_name: Optional[str] = None
  upload_quota_used: int = 0
  mfa_enabled: bool = False
  model_config = ConfigDict(from_attributes=True)


# Внутренняя схема для сервисного слоя. Не использовать в роутерах.
class UserInDB(UserRead):
  password_hash: str
  role_id: int
  mfa_secret: Optional[str] = None
  failed_login_attempts: int = 0
  model_config = ConfigDict(from_attributes=True)
