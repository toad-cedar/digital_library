# app/api/routers/uploads.py
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.integrations.minio_client   import minio_client
from app.integrations.elastic_client import elastic_client
from app.services.upload_service import UploadService
from app.services.minio_service  import MinioService
from app.services.search_service import SearchService
from app.config.database  import get_db_session
from app.config.deps      import get_current_user
from app.schemas.upload   import UploadRequestCreate, UploadRequestOut
from app.schemas.document import DocumentCreate
from app.models.orm_models import User
from app.repos.status_repo import StatusRepository

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post("/", summary="Загрузить документ")
async def upload_document(
  title: str = Form(...),
  description: str = Form(None),
  author: str = Form(None),
  tags: str = Form(""), # Принимаем строку с тегами, разделёнными запятой
  file: UploadFile = File(...),
  current_user: User = Depends(get_current_user),
  db_session: AsyncSession = Depends(get_db_session),
):
  """
  Загружает файл в систему.
  - Проверяет дубликат по хешу.
  - Сохраняет в MinIO.
  - Создаёт запись в БД (одобренный статус).
  - Индексирует в Elasticsearch.
  """
  # 1. Прочитать файл в память
  file_content = await file.read()
  if not file_content:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

  # 2. Разбор тегов
  tag_list = [t.strip() for t in tags.split(",") if t.strip()]

  # 3. Подготовка сервисов
  minio_service = MinioService()
  search_service = SearchService()
  status_repo = StatusRepository(db_session)
  upload_service = UploadService(
    db_session=db_session,
    minio_service=minio_service,
    search_service=search_service,
    status_repo=status_repo
  )

  # 4. Обработка через сервис
  result = await upload_service.process_upload(
    file_bytes=file_content,
    original_filename=file.filename,
    user=current_user,
    document_title=title,
    document_description=description,
    document_author=author,
    tags=tag_list,
  )

  return result

# Роутеры для получения статуса загрузки и списка загрузок пользователя
# (в мин. версии может быть не нужно, но оставлю заготовку)
# @router.get("/", response_model=List[UploadRequestOut], summary="Получить список моих загрузок")
# async def get_my_uploads(
#     current_user: User = Depends(get_current_user),
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     # ... реализация получения UploadRequest из БД по user_id
#     pass
#
# @router.get("/{upload_id}", response_model=UploadRequestOut, summary="Получить статус загрузки")
# async def get_upload_status(
#     upload_id: int,
#     current_user: User = Depends(get_current_user), # или админ
#     db_session: AsyncSession = Depends(get_db_session)
# ):
#     # ... реализация получения конкретной UploadRequest
#     pass