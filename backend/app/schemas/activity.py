from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ViewHistoryRead(BaseModel):
  id: int
  user_id: int
  document_id: int
  viewed_at: datetime
  model_config = ConfigDict(from_attributes=True)


class DownloadHistoryRead(BaseModel):
  id: int
  user_id: int | None
  document_id: int
  downloaded_at: datetime
  ip_address: str | None
  user_agent: str | None
  download_type: str  # preview / full / export
  is_success: bool
  model_config = ConfigDict(from_attributes=True)


class UserStatisticsResponse(BaseModel):
  total_views: int
  total_downloads: int
  last_active_at: datetime | None
  most_viewed_format: str | None
  activity_summary: dict[str, int]  # например: {"day": 5, "week": 34}
  model_config = ConfigDict(from_attributes=True)