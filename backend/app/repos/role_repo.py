from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.orm_models import Role

class RoleRepository:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
  
  async def get_role_id_by_name(self, role_name: str) -> Optional[int]:
    """Получает ID роли по имени."""
    stmt = select(Role.id).where(Role.role_name == role_name)
    result = await self.db_session.execute(stmt)
    return result.scalar_one_or_none()