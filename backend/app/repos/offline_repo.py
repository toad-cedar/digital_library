from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.offline_models import OfflineFolder, OfflineItem
from app.models.system_models import SyncState, RegistryDevice
from app.repos.base_repo import GenericRepository


class OfflineRepository:
  def __init__(self, db_session: AsyncSession):
    self.db = db_session
    self.folders = GenericRepository(db_session, OfflineFolder)
    self.items = GenericRepository(db_session, OfflineItem)
    self.syncs = GenericRepository(db_session, SyncState)
    self.devices = GenericRepository(db_session, RegistryDevice)

  async def get_folder(self, folder_id: int) -> Optional[OfflineFolder]:
    return await self.folders.get_by_id(folder_id)

  async def create_folder(self, folder: OfflineFolder) -> OfflineFolder:
    return await self.folders.create(folder)

  async def delete_folder(self, folder_id: int) -> bool:
    return await self.folders.delete(folder_id)

  async def add_item(self, item: OfflineItem) -> OfflineItem:
    return await self.items.create(item)

  async def remove_item(self, document_id: int, folder_id: int) -> bool:
    stmt = delete(OfflineItem).where(OfflineItem.document_id == document_id, OfflineItem.folder_id == folder_id)
    return (await self.db.execute(stmt)).rowcount > 0

  async def get_device(self, device_uuid: str) -> Optional[RegistryDevice]:
    stmt = select(RegistryDevice).where(RegistryDevice.device_uuid == device_uuid)
    return (await self.db.execute(stmt)).scalar_one_or_none()

  async def update_device_heartbeat(self, device_uuid: str) -> None:
    stmt = update(RegistryDevice).where(RegistryDevice.device_uuid == device_uuid).values(last_heartbeat=datetime.now(timezone.utc))
    await self.db.execute(stmt)

  async def get_sync_states(self, user_id: int, device_id: int) -> List[SyncState]:
    stmt = select(SyncState).where(SyncState.user_id == user_id, SyncState.device_id == device_id)
    return (await self.db.execute(stmt)).scalars().all()

  async def upsert_sync_state(self, state: SyncState) -> SyncState:
    stmt = update(SyncState).where(
      SyncState.user_id == state.user_id,
      SyncState.device_id == state.device_id,
      SyncState.entity_type == state.entity_type,
      SyncState.entity_id == state.entity_id
    ).values(
      local_checksum=state.local_checksum,
      server_checksum=state.server_checksum,
      network_status=state.network_status,
      last_sync_at=state.last_sync_at,
      conflict_resolution=state.conflict_resolution
    ).returning(SyncState)
    
    result = await self.db.execute(stmt)
    obj = result.scalar_one_or_none()
    if obj:
      return obj
    self.db.add(state)
    await self.db.flush()
    return state