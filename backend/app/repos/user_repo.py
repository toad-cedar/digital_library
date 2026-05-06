# app/repositories/user_repo.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.orm_models import User


class UserRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session

  async def get_by_id(self, user_id: int) -> Optional[User]:
    """Получает пользователя по ID."""
    stmt = select(User).where(User.id == user_id)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_by_username(self, username: str) -> Optional[User]:
    """Получает пользователя по имени пользователя (username)."""
    stmt = select(User).where(User.username == username)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def get_by_email(self, email: str) -> Optional[User]:
    """Получает пользователя по email."""
    stmt = select(User).where(User.email == email)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()

  async def create(self, user: User) -> User:
    """Создаёт нового пользователя."""
    self.db_session.add(user)
    await self.db_session.flush() # Получаем ID без коммита всей транзакции
    return user

  async def update(self, user_id: int, update_data: dict) -> Optional[User]:
    """Обновляет пользователя по ID."""
    # Используем SQLAlchemy Core для обновления, так как ORM update требует объект
    stmt = (
      update(User)
      .where(User.id == user_id)
      .values(**update_data)
      .returning(User) # Возвращаем обновлённый объект
    )
    result = await self.db_session.execute(stmt)
    updated_user = result.scalar_one_or_none()
    if updated_user:
      await self.db_session.commit()
      await self.db_session.refresh(updated_user) # Обновляем объект из БД
    else:
      await self.db_session.rollback() # Откатываем, если ничего не обновилось
    return updated_user

  async def delete(self, user_id: int) -> bool:
    """Удаляет пользователя по ID."""
    stmt = delete(User).where(User.id == user_id)
    result = await self.db_session.execute(stmt)
    if result.rowcount > 0:
      await self.db_session.commit()
      return True
    else:
      await self.db_session.rollback()
      return False

  # Пример метода для получения списка пользователей с пагинацией
  # async def get_users(self, offset: int = 0, limit: int = 10) -> List[User]:
  #     stmt = select(User).offset(offset).limit(limit)
  #     result = await self.db_session.execute(stmt)
  #     return result.scalars().all()
