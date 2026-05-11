from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class UploadRequestRead(BaseModel):
  id: int
  title: str
  uploader_id: int
  file_original_name: Optional[str] = None
  file_mime: str
  file_size: int
  file_hash: str
  workflow_status: str
  rejection_reason: Optional[str] = None
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)

class UploadStatusResponse(BaseModel):
  upload_id: int
  workflow_status: str
  processing_stage: Optional[str] = None  # e.g., "scanning", "ocr", "indexing"

class ProcessingMetadata(BaseModel):
  risk_score: int = 0
  ocr_text_found: bool = False
  mime_validated: bool = True
  conversion_triggered: bool = False