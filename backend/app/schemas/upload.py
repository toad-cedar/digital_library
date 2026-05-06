from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadRequestCreate(BaseModel):
  original_name: str
  file_hash: str
  # остальные поля заполняются бэкендом: user_id, minio_path, status, upload_date


class UploadRequestOut(BaseModel):
  id: int
  user_id: int
  original_name: str
  minio_path: str
  upload_date: datetime
  file_hash: str
  status_id: int
  moderator_id: Optional[int] = None

  class Config:
    from_attributes = True