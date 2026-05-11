from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.user_models import User
from app.config.database import AccountEnum
from app.repos.base_repo import GenericRepository


class UserRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.base = GenericRepository(db_session, User)

  async def get_by_id(self, user_id: int) -> Optional[User]:
    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_by_username(self, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_by_email(self, email: str) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def create(self, user: User) -> User:
    return await self.base.create(user)

  async def update(self, user_id: int, data: dict) -> Optional[User]:
    return await self.base.update(user_id, data)

  async def delete(self, user_id: int) -> bool:
    return await self.base.delete(user_id)

  async def get_list(
    self,
    account_status: Optional[AccountEnum] = None,
    offset: int = 0,
    limit: int = 10
  ) -> Tuple[List[User], int]:
    stmt = select(User).options(selectinload(User.role))
    count_stmt = select(func.count(User.id))

    if account_status is not None:
      stmt = stmt.where(User.account_status == account_status)
      count_stmt = count_stmt.where(User.account_status == account_status)

    total = (await self.db_session.execute(count_stmt)).scalar() or 0
    users = (await self.db_session.execute(
      stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
    )).scalars().all()
    return users, total