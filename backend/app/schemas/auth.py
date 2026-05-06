from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re # regex

class Token(BaseModel):
  access_token: str
  token_type: str

class TokenData(BaseModel):
  username: Optional[str] = None

class UserLogin(BaseModel):
  username: str
  password: str

class UserCreate(BaseModel):
  username: str
  email: EmailStr
  password: str

  @field_validator('username')
  def validate_username(cls, v):
    # Проверка формата username: строчный, 3-100 символов, только буквы, цифры, подчеркивание, начинается с буквы
    if not re.match(r'^[a-z][a-z0-9_]{2,99}$', v):
      raise ValueError('Username must start with a letter, contain 3-100 characters, and include only lowercase letters, numbers, and underscores.')
    if 'admin' in v.lower() or 'root' in v.lower():
      raise ValueError('Username cannot contain "admin" or "root".')
    return v

  @field_validator('password')
  def validate_password(cls, v):
    # Простая проверка сложности пароля (длина, наличие заглавной, строчной, цифры, символа)
    if len(v) < 8:
      raise ValueError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', v):
      raise ValueError('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', v):
      raise ValueError('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', v):
      raise ValueError('Password must contain at least one digit.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
      raise ValueError('Password must contain at least one special character.')
    return v