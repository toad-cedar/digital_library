from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db_session
from app.config.deps import get_current_user, get_minio
from app.auth.casbin.dependencies import require_permission
from app.auth.casbin.service import CasbinService
from app.auth.permissions import Permissions
from app.models.user_models import User
from app.services.moderation_service import ModerationService
from app.services.minio_service import MinioService
from app.schemas import ApiResponse, ModerationDecision, ReportCreate, ReportRead, ModerationQueueResponse


router = APIRouter(prefix="/api/v1/moderation", tags=["Moderation"])

@router.get("/queue", response_model=ApiResponse[ModerationQueueResponse])
async def get_queue(
  page: int = Query(1, ge=1),
  page_size: int = Query(20, ge=1, le=100),
  current_user: User = Depends(get_current_user),
  _: None = Depends(lambda: require_permission(Permissions.UPLOAD_REVIEW)),
  db_session: AsyncSession = Depends(get_db_session)
):
  
  try:
    svc = ModerationService(db_session=db_session, minio_service=get_minio())
    return ApiResponse(success=True, data=await svc.get_queue(page, page_size))
  except Exception as e:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/queue/{upload_id}/decision", response_model=ApiResponse[dict])
async def process_decision(
  upload_id: int,
  data: ModerationDecision,
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session)
):
  # Динамическая проверка прав после парсинга тела запроса
  action = "approve" if data.decision == "approve" else "reject"
  if not CasbinService.enforce(str(current_user.id), "moderation", action):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

  try:
    svc = ModerationService(db_session=db_session, minio_service=get_minio())
    await svc.process_decision(upload_id, current_user.id, data)
    return ApiResponse(success=True, data={"status": "processed"})
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/documents/{document_id}/report", response_model=ApiResponse[ReportRead])
async def create_report(
  document_id: int,
  data: ReportCreate,
  current_user: User = Depends(get_current_user),
  _: None = Depends(lambda: require_permission(Permissions.DOCUMENT_REPORT)),
  db_session: AsyncSession = Depends(get_db_session)
):
  try:
    svc = ModerationService(db_session=db_session, minio_service=get_minio())
    return ApiResponse(success=True, data=await svc.handle_report(
      reporter_id=current_user.id, 
      target_type="document",
      target_id=document_id, 
      category=data.reason_category, 
      description=data.description
    ))
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))