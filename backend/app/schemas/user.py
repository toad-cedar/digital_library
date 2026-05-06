from pydantic import BaseModel

class UserOut(BaseModel):
  id: int
  username: str
  email: str
  current_status: bool

  class Config:
    from_attributes = True


class UserInDB(UserOut):
  password_hash: str
  user_role_id: int

  class Config:
    from_attributes = True


class UserShort(BaseModel):
  id: int
  username: str
  
  class Config:
    from_attributes = True