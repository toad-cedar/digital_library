from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.settings import get_settings

# Контекст для хеширования паролей (passlib)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
  """Проверяет, соответствует ли plain_password хешированному hashed_password."""
  return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
  """Хеширует пароль."""
  return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
  """Создаёт JWT-токен."""
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(timezone.utc) + timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)

  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
    to_encode,
    get_settings().SECRET_KEY,
    algorithm=get_settings().ALGORITHM
  )
  return encoded_jwt

def decode_access_token(token: str) -> dict:
  """Декодирует JWT-токен и возвращает payload."""
  try:
    payload = jwt.decode(token, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      return None
    return payload
  except JWTError:
    return None