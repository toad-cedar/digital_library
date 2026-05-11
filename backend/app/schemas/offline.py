from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List
from uuid import UUID


class OfflineFolderCreate(BaseModel):
  folder_name: str = Field(min_length=1, max_length=100)
  description: str | None = Field(None, max_length=500)
  parent_folder_id: int | None = None


class OfflineFolderRead(BaseModel):
  id: int
  folder_name: str
  description: str | None
  parent_folder_id: int | None
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)


class OfflineFolderUpdate(BaseModel):
  folder_name: str | None = Field(None, min_length=1, max_length=100)
  description: str | None = Field(None, max_length=500)
  parent_folder_id: int | None = None


class OfflineItemAdd(BaseModel):
  document_id: int


class LocalStateItem(BaseModel):
  entity_type: str
  entity_id: UUID
  local_checksum: str = Field(min_length=64, max_length=64)
  network_status: str  # synced / pending / conflict / deleted_locally


class SyncConfigRequest(BaseModel):
  device_uuid: UUID
  device_info: dict[str, str]  # {"platform": "...", "app_version": "..."}
  local_state: List[LocalStateItem]


class ConflictResolutionItem(BaseModel):
  entity_id: UUID
  strategy: str  # server_wins / client_wins / merge


class SyncStateResponse(BaseModel):
  server_state: List[dict]
  conflict_resolutions: List[ConflictResolutionItem]
  sync_token: str