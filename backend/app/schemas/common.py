from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Any, List

T = TypeVar("T")


class PaginationParams(BaseModel):
  page: int = Field(1, ge=1)
  page_size: int = Field(20, ge=1, le=100)


class PaginationResponse(BaseModel, Generic[T]):
  data: List[T]
  total: int
  page: int
  page_size: int


class ApiResponse(BaseModel, Generic[T]):
  success: bool = True
  data: T | None = None
  message: str | None = None


class ErrorDetail(BaseModel):
  code: str
  message: str
  details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
  success: bool = False
  error: ErrorDetail