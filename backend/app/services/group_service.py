from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.group_repo import GroupRepository
from app.repos.user_repo import UserRepository
from app.schemas.group import (
  GroupCreate, GroupRead, GroupUpdate, MemberAddRequest,
  InviteRequest, InviteAcceptRequest, InviteResponse
)
from app.models.group_models import Group, GroupInvitation  
from app.config.database import InvitationEnum
import uuid


class GroupService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.group_repo = GroupRepository(db_session)
    self.user_repo = UserRepository(db_session)

  async def create(self, creator_id: int, data: GroupCreate) -> GroupRead:
    group = Group(group_name=data.group_name, creator_id=creator_id)
    created = await self.group_repo.create(group)
    await self.db_session.commit()
    return GroupRead.model_validate(created)

  async def update(self, group_id: int, creator_id: int, data: GroupUpdate) -> GroupRead:
    group = await self.group_repo.get_by_id(group_id)
    if not group or group.creator_id != creator_id:
      raise ValueError("Group not found or access denied")
        
    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    updated = await self.group_repo.update(group_id, update_data)
    await self.db_session.commit()
    return GroupRead.model_validate(updated)

  async def invite(self, group_id: int, creator_id: int, data: InviteRequest) -> InviteResponse:
    group = await self.group_repo.get_by_id(group_id)
    if not group or group.creator_id != creator_id:
        raise ValueError("Group not found or access denied")
        
    token = str(uuid.uuid4())
    invitation = GroupInvitation(
        group_id=group_id,
        invited_email=data.invited_email,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_by=creator_id,
        invitation_status=InvitationEnum.PENDING
    )
    await self.group_repo.db.add(invitation)
    await self.db.commit()
    
    return InviteResponse(token=token, message="Invitation created")

  async def accept_invite(self, data: InviteAcceptRequest) -> bool:
    invite = await self.group_repo.get_invitation_by_token(data.token)
    if not invite or invite.invitation_status != InvitationEnum.PENDING:
      raise ValueError("Invalid or expired token")
    if invite.expires_at < datetime.now(timezone.utc):
      raise ValueError("Token expired")
        
    user = await self.user_repo.get_by_email(invite.invited_email)
    if not user:
      raise ValueError("User with invited email not found")
    
    await self.group_repo.add_member(invite.group_id, user.id)
    await self.group_repo.update_invitation_status(invite.id, InvitationEnum.ACCEPTED)
    await self.db_session.commit()
    return True

  async def add_member(self, group_id: int, creator_id: int, data: MemberAddRequest) -> bool:
    group = await self.group_repo.get_by_id(group_id)
    if not group or group.creator_id != creator_id:
      raise ValueError("Group not found or access denied")
    
    await self.group_repo.add_member(group_id, data.user_id)
    await self.db_session.commit()
    return True