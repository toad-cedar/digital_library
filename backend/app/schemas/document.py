from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional

class DocumentRead(BaseModel):
  id: int
  title: str
  description: Optional[str] = None
  publish_date: datetime
  uploader_id: int
  minio_bucket: str
  file_original_name: Optional[str] = None
  file_mime: str
  file_size: int
  file_hash: str
  format: str
  converted_to_pdf: bool
  visibility_status: str
  created_at: datetime
  model_config = ConfigDict(from_attributes=True)

class DocumentCreate(BaseModel):
  title: str = Field(min_length=1, max_length=255)
  description: Optional[str] = None
  tag_names: List[str] = []

class DocumentUpdate(BaseModel):
  title: Optional[str] = Field(None, min_length=1, max_length=255)
  description: Optional[str] = None
  tag_names: Optional[List[str]] = None

class VisibilityUpdate(BaseModel):
  visibility_status: str # published | unlisted | archived

class TagAssignRequest(BaseModel):
  tags: List[str]

class VersionRead(BaseModel):
  version_number: int
  created_at: datetime
  file_format: str
  file_size: int
  change_notes: Optional[str] = None
  model_config = ConfigDict(from_attributes=True)

class DownloadUrlResponse(BaseModel):
  url: str
  expires_at: datetime

class DocumentListResponse(BaseModel):
  documents: List[DocumentRead]
  total: int
  page: int # offset: int
  page_size: int # limit: int