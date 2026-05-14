from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert, delete, update
from app.models.group_models import Group, GroupMaterial, GroupInvitation, groups_users
from app.repos.base_repo import GenericRepository
from app.config.database import InvitationEnum


class GroupRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.base = GenericRepository(db_session, Group)

  async def get_by_id(self, group_id: int) -> Optional[Group]:
    return await self.base.get_by_id(group_id)

  async def create(self, group: Group) -> Group:
    return await self.base.create(group)

  async def update(self, group_id: int, data: dict) -> Optional[Group]:
    return await self.base.update(group_id, data)

  async def delete(self, group_id: int) -> bool:
    return await self.base.delete(group_id)

  async def add_member(self, group_id: int, user_id: int) -> None:
    stmt = insert(groups_users).values(group_id=group_id, user_id=user_id)
    await self.db.execute(stmt)

  async def remove_member(self, group_id: int, user_id: int) -> bool:
    stmt = delete(groups_users).where(groups_users.c.group_id == group_id, groups_users.c.user_id == user_id)
    return (await self.db.execute(stmt)).rowcount > 0

  async def get_materials(self, group_id: int, offset: int = 0, limit: int = 10) -> Tuple[List[GroupMaterial], int]:
    base = select(GroupMaterial).where(GroupMaterial.group_id == group_id)
    count = (await self.db.execute(select(func.count(GroupMaterial.id)).where(GroupMaterial.group_id == group_id))).scalar() or 0
    items = (await self.db.execute(base.offset(offset).limit(limit))).scalars().all()
    return items, count

  async def get_invitation_by_token(self, token: str) -> Optional[GroupInvitation]:
    stmt = select(GroupInvitation).where(GroupInvitation.token == token)
    return (await self.db.execute(stmt)).scalar_one_or_none()
  
  async def update_invitation_status(self, invitation_id: int, status: InvitationEnum) -> Optional[GroupInvitation]:
    stmt = update(GroupInvitation).where(GroupInvitation.id == invitation_id).values(invitation_status=status).returning(GroupInvitation)
    result = await self.db.execute(stmt)
    return result.scalar_one_or_none()