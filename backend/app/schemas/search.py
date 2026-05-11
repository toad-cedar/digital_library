from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class SearchRequest(BaseModel):
  q: str = Field("", min_length=1)
  page: int = Field(1, ge=1)
  page_size: int = Field(20, ge=1, le=100)
  tags: Optional[List[str]] = None
  format: Optional[str] = None
  date_from: Optional[datetime] = None
  date_to: Optional[datetime] = None

class SearchResponseItem(BaseModel):
  id: int
  title: str
  description: Optional[str] = None
  publish_date: datetime
  format: str
  file_size: int
  tags: List[str]
  uploader_name: str
  snippet: Optional[str] = None
  model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
  items: List[SearchResponseItem]
  total: int
  page: int
  page_size: int