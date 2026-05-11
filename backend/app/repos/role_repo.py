from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.user_models import Role
from app.repos.base_repo import GenericRepository


class RoleRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.base = GenericRepository(db_session, Role)

  async def get_by_id(self, role_id: int) -> Optional[Role]:
    stmt = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_by_name(self, name: str) -> Optional[Role]:
    stmt = select(Role).where(Role.role_name == name)
    return (await self.db_session.execute(stmt)).scalar_one_or_none()

  async def get_all(self, offset: int = 0, limit: int = 10) -> Tuple[List[Role], int]:
    base = select(Role)
    total = (await self.db_session.execute(select(func.count(Role.id)))).scalar() or 0
    items = (await self.db_session.execute(base.offset(offset).limit(limit))).scalars().all()
    return items, total

  async def create(self, role: Role) -> Role:
    return await self.base.create(role)

  async def update(self, role_id: int, data: dict) -> Optional[Role]:
    return await self.base.update(role_id, data)

  async def delete(self, role_id: int) -> bool:
    return await self.base.delete(role_id)