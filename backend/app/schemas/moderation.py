from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Literal, List


class ModerationQueueItem(BaseModel):
  id: int
  title: str
  uploader_id: int
  file_mime: str
  file_size: int
  workflow_status: str
  created_at: datetime
  priority_score: int | None
  deadline: datetime | None
  model_config = ConfigDict(from_attributes=True)


class ModerationQueueResponse(BaseModel):
  items: List[ModerationQueueItem]
  total: int
  page: int
  page_size: int


class ModerationDecision(BaseModel):
  decision: Literal["approve", "reject"]
  reason: str | None = Field(None, max_length=1000)


class ReportCreate(BaseModel):
  reason_category: str = Field(..., pattern="^(copyright|inappropriate|virus|other)$")
  description: str | None = Field(None, max_length=2000)


class ReportRead(BaseModel):
  id: int
  reporter_id: int
  target_type: str  # document / user / group
  target_id: int
  reason_category: str
  description: str | None
  report_status: str
  created_at: datetime
  resolved_at: datetime | None
  resolved_by: int | None
  resolution_note: str | None
  model_config = ConfigDict(from_attributes=True)


class AssignmentRead(BaseModel):
  id: int
  upload_requests_id: int
  moderator_id: int
  deadline: datetime
  priority_score: int
  assigned_at: datetime
  completed_at: datetime | None
  model_config = ConfigDict(from_attributes=True)