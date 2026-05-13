from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.integrations.minio_client import get_minio_client
from app.integrations.elastic_client import get_elastic_client
from app.config.database import get_db_session
from app.config.settings import get_settings
from app.models import User
from app.repos.user_repo import UserRepository


security = HTTPBearer()

def get_minio():
  return get_minio_client()

def get_elastic():
  return get_elastic_client()


async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  db_session: AsyncSession = Depends(get_db_session)
) -> User:
  """
  Зависимость для получения текущего аутентифицированного пользователя из токена.
  """
  unauthorized_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )

  try:
    payload = jwt.decode(credentials.credentials, get_settings().SECRET_KEY, algorithms=[get_settings().ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
      raise unauthorized_exception
  except JWTError:
    raise unauthorized_exception

  user_repo = UserRepository(db_session)
  user = await user_repo.get_by_username(username)
  if user is None:
    raise unauthorized_exception
  if not user.current_status:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User account is deactivated"
    )

  return user





# Зависимости для проверки ролей (пример)
# async def get_current_active_user(current_user: User = Depends(get_current_user)):
#     if not current_user.current_status:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user

# async def get_current_admin_user(current_user: User = Depends(get_current_user)):
#     if current_user.role.role_name != "admin":
#         raise HTTPException(status_code=403, detail="Admin privileges required")
#     return current_user

# async def get_current_teacher_or_admin_user(current_user: User = Depends(get_current_user)):
#     if current_user.role.role_name not in ("teacher", "admin"):
#         raise HTTPException(status_code=403, detail="Teacher or Admin privileges required")
#     return current_user