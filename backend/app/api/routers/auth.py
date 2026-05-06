from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.user_repo import UserRepository
from app.repos.role_repo import RoleRepository
from app.config.database import get_db_session
from app.config.security import create_access_token, hash_password, verify_password
from app.config.deps     import get_current_user
from app.models.orm_models import User
from app.schemas.auth    import UserLogin, UserCreate, Token
from app.schemas.user    import UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut)
async def register(
  user_data: UserCreate,
  db_session: AsyncSession = Depends(get_db_session)
):
  """
  Регистрация нового пользователя c, по умолчанию, ролью user
  """
  user_repo = UserRepository(db_session)
  role_repo = RoleRepository(db_session)

  # Проверка на существование пользователя по username или email
  existing_user_by_username = await user_repo.get_by_username(user_data.username)
  if existing_user_by_username:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Username already registered"
    )

  existing_user_by_email = await user_repo.get_by_email(user_data.email)
  if existing_user_by_email:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Email already registered"
    )
  
  # Получение ID роли user по имени
  user_role_id = await role_repo.get_role_id_by_name("user")
  if not user_role_id:
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Default role 'user' not found in database"
    ) 
  
  # Хеширование пароля
  hashed_password = hash_password(user_data.password)
  
  # Создание нового пользователя
  new_user = User(
    username     =user_data.username,
    email        =user_data.email,
    password_hash=hashed_password,
    user_role_id =user_role_id,
  )

  created_user = await user_repo.create(new_user)
  await db_session.commit()
  await db_session.refresh(created_user)

  # Возвращаем только основную информацию, не пароль
  return UserOut.model_validate(created_user)

@router.post("/login", response_model=Token)
async def login(
  user_data: UserLogin,
  db_session: AsyncSession = Depends(get_db_session)
):
  """
  Аутентификация пользователя и выдача JWT-токена.
  """
  user_repo = UserRepository(db_session)

  # Поиск пользователя по username
  user = await user_repo.get_by_username(user_data.username)
  if not user or not verify_password(user_data.password, user.password_hash):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Incorrect username or password",
      headers={"WWW-Authenticate": "Bearer"},
    )

  # Проверка статуса пользователя
  if not user.current_status:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User account is deactivated"
    )

  # Создание токена
  access_token = create_access_token(
    data={"sub": user.username}
  ) 

  return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout", summary="Выход из системы", response_model=Token)
async def logout(current_user: User = Depends(get_current_user)):
  """
  Выход из системы. Удаляет активный токен на стороне клиента
  """
  # В простой реализации JWT (stateless) сервер не хранит активные токены.
  # Задача logout - убедиться, что клиент удалил токен.
  # Сервер может вернуть успешный ответ, подтверждая, что запрос был обработан.
  # Для реализации "отзыва" токена (blacklist) потребуется хранение токенов (например, в Redis или БД).
  return { "message": "Logged out"} # Клиент ожидает этот ответ, чтобы затем очистить свой localStorage и store.
