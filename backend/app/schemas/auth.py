from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re

class LoginRequest(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8)

class RegisterRequest(BaseModel):
  username: str = Field(min_length=3, max_length=100, pattern=r"^[a-z][a-z0-9_]{2,99}$")
  email: EmailStr
  password: str = Field(min_length=8)
  
  @field_validator('password')
  @classmethod
  def check_password_complexity(cls, v: str) -> str:
    if not re.search(r'[A-Z]', v): raise ValueError("Требуется заглавная буква")
    if not re.search(r'[a-z]', v): raise ValueError("Требуется строчная буква")
    if not re.search(r'\d', v):    raise ValueError("Требуется цифра")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v): raise ValueError("Требуется спецсимвол")
    if 'admin' in v.lower() or 'root' in v.lower(): raise ValueError("Пароль содержит запрещённые слова")
    return v

class TokenResponse(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str = "bearer"
  model_config = ConfigDict(
    json_schema_extra=
    {
      "example": 
      {
        "access_token": "...", 
        "refresh_token": "..."
      }
    } 
  )

class RefreshRequest(BaseModel):
  refresh_token: str

class RecoveryRequest(BaseModel):
  email: EmailStr

class ResetPasswordRequest(BaseModel):
  token: str
  new_password: str = Field(min_length=8)

class MfaVerifyRequest(BaseModel):
  code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")