from pydantic import BaseModel
from typing import Optional

class SearchQuery(BaseModel):
  query: str
  filters: Optional[dict] = None # {"author": "...", "date_from": "...", "tags": ["..."]}
  offset: int = 0
  limit: int = 10