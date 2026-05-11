from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID


class NotificationRead(BaseModel):
  id: int
  user_id: int
  source_type: str
  source_id: int
  event_type: str
  title: str
  content: dict
  channel: str  # in_app / email
  is_read: bool
  read_at: datetime | None
  created_at: datetime
  expires_at: datetime
  model_config = ConfigDict(from_attributes=True)


class NotificationMarkRead(BaseModel):
  # Тело запроса не требуется, ID уведомления передаётся в path
  pass


class AuditLogRead(BaseModel):
  id: int
  user_id: int
  action: str
  target_uuid: UUID
  target_type: str
  details: dict
  ip_address: str | None
  success: bool
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
  user_id: int | None = None
  action: str | None = None
  target_type: str | None = None
  from_date: datetime | None = None
  to_date: datetime | None = None
  page: int = Field(1, ge=1)
  page_size: int = Field(20, ge=1, le=100)


class HealthStatus(BaseModel):
  api: str
  database: str
  minio: str
  elasticsearch: str
  redis: str = "ok"


class HealthResponse(BaseModel):
  success: bool = True
  data: HealthStatus


class DeviceRegister(BaseModel):
  device_uuid: UUID
  device_name: str = Field(min_length=1, max_length=100)
  platform: str = Field(min_length=1, max_length=20)
  app_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")