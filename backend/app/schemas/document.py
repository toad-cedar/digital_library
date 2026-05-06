from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.user import UserShort

class StatusInfo(BaseModel): # для информации о статусе
  id: int
  name: str

class FormatInfo(BaseModel):
  id: int
  name: str

class DocumentOut(BaseModel):
  id: int
  title: str
  description: Optional[str] = None
  author: Optional[str] = None
  upload_date: datetime
  publish_date: datetime
  uploader: UserShort
  minio_bucket: str # Бакет основного файла
  cover_bucket: Optional[str] = None # Бакет обложки
  format: FormatInfo
  file_original_name: Optional[str] = None
  file_size: int
  converted_to_pdf: bool
  status_name: StatusInfo 
  tags: List[str]
  cover_url: Optional[str] = None # обложка
  
  class Config:
    from_attributes = True


class DocumentListResponse(BaseModel):
  total: int
  offset: int
  limit: int
  documents: List[DocumentOut]
  
  class Config:
    from_attributes = True


class PreviewUrlResponse(BaseModel):
  url: str
  expires_at: datetime
  
  class Config:
    from_attributes = True


class DocumentCreate(BaseModel):
  title: str
  description: Optional[str] = None
  author: Optional[str] = None
  tag_names: List[str]
  # Поля, которые заполняются бэкендом: uploader_id (из токена), upload_date, file_* и т.д.
  # Эти поля не передаются из API.


class DocumentUpdate(BaseModel):
  title: Optional[str] = None
  description: Optional[str] = None
  author: Optional[str] = None
  tag_names: Optional[List[str]] = None

  class Config:
    extra = 'forbid'