from sqlalchemy.ext.asyncio import AsyncSession
from app.repos.offline_repo import OfflineRepository
from app.schemas.offline import SyncConfigRequest, SyncStateResponse, ConflictResolutionItem
from app.models.system_models import RegistryDevice
import logging
import uuid


logger = logging.getLogger(__name__)

class OfflineService:
  def __init__(self, db_session: AsyncSession):
    self.db_session = db_session
    self.offline_repo = OfflineRepository(db_session)

  async def register_device(self, user_id: int, data: SyncConfigRequest) -> RegistryDevice:
    device = await self.offline_repo.get_device(data.device_uuid)
    if not device:
      device = RegistryDevice(
        user_id=user_id, 
        device_uuid=data.device_uuid,
        device_name=data.device_info.get("device_name", "Unknown"),
        platform=data.device_info.get("platform", "unknown"),
        app_version=data.device_info.get("app_version", "0.0.0")
      )
      await self.db_session.add(device)
    else:
      await self.offline_repo.update_device_heartbeat(device.device_uuid)
      
    await self.db_session.commit()
    return device

  async def sync(self, user_id: int, config: SyncConfigRequest) -> SyncStateResponse:
    device = await self.register_device(user_id, config)
    server_states = await self.offline_repo.get_sync_states(user_id, device.id)
    
    conflicts = []
    for local in config.local_state:
      matched = next((s for s in server_states if s.entity_id == local.entity_id), None)
      if matched and matched.server_checksum != local.local_checksum:
        conflicts.append({"entity_id": local.entity_id, "strategy": "server_wins"})
    
    clean_states = [
      {k: v for k, v in s.__dict__.items() if not k.startswith("_")} 
      for s in server_states
    ]
    
    return SyncStateResponse(
      server_state=clean_states,
      conflict_resolutions=[ConflictResolutionItem(**c) for c in conflicts],
      sync_token=str(uuid.uuid4())
    )