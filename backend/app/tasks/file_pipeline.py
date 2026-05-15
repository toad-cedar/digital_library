import logging
import os
import tempfile
import traceback
import boto3
from datetime import datetime, timezone
from rq import get_current_job
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from botocore.exceptions import ClientError

from app.core.sync_db import SyncSessionLocal
from app.config.settings import get_settings
from app.config.database import VisibilityEnum, WorkflowEnum, ConversionEnum
from app.models.user_models import User
from app.models.processing_models import ConversionJob
from app.models.document_models import Document, UploadRequest
from app.services.risk_analyzer import RiskAnalyzer
from app.services.file_validator import FileValidator, FileValidationError
from app.services.text_extractor import extract_text, TextExtractionError
from app.services.pdf_converter import convert_to_pdf_sync, needs_conversion


logger = logging.getLogger(__name__)

def _get_sync_s3() -> boto3.client:
  """Возвращает синхронный S3-клиент для использования внутри RQ-воркеров"""
  settings = get_settings()
  return boto3.client(
    's3',
    endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    verify=settings.VERIFY_TLS
  )

def _cleanup_temp_file_direct(s3: boto3.client, temp_key: str) -> None:
  """Удаляет файл из временного бакета без загрузки записи из БД"""
  if not temp_key:
    return
  try:
    s3.delete_object(Bucket="temporary", Key=temp_key)
    logger.info(f"Temporary file cleaned: {temp_key}")
  except ClientError as e:
    # Файл уже удалён или нет прав — не считаем это критичной ошибкой
    logger.warning(f"Failed to clean temp file {temp_key}: {e}")

def _update_job_error(session: Session, upload_id: int, error: Exception, context: str, retries_left: int | None) -> None:
  """Записывает ошибку, инкрементирует retry_count и обновляет статус в conversion_jobs"""
  stmt = select(ConversionJob).where(
    ConversionJob.source_entity_id == upload_id
  ).order_by(ConversionJob.id.desc()).limit(1)
  job_record = session.execute(stmt).scalar_one_or_none()

  if not job_record:
    job_record = ConversionJob(source_entity_id=upload_id, conversion_status=ConversionEnum.PENDING)
    session.add(job_record)
    session.flush()

  max_retries = 3
  current_left = retries_left if retries_left is not None else 0
  job_record.retry_count = max(job_record.retry_count, max(0, max_retries - current_left))
  
  timestamp = datetime.now(timezone.utc).isoformat()
  job_record.error_log = (job_record.error_log or "") + f"\n[{timestamp}] {context}: {str(error)}\n{traceback.format_exc()}"

  if job_record.retry_count >= max_retries:
    job_record.conversion_status = ConversionEnum.FAILED
    upload = session.get(UploadRequest, upload_id)
    if upload:
      upload.workflow_status = WorkflowEnum.REJECTED
      upload.rejection_reason = f"Pipeline failed after retries: {context}"
  else:
    job_record.conversion_status = ConversionEnum.RETRYING
  
  session.commit()

def validate_file_task(upload_id: int) -> None:
  """
  Скачивает файл из временного бакета, проверяет размер, magic bytes, 
  MIME-тип и расширение. При успехе переводит статус в PROCESSING.
  """
  job = get_current_job()
  session = SyncSessionLocal()
  temp_path = None
  s3 = _get_sync_s3()
  
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status in (WorkflowEnum.ACCEPTED, WorkflowEnum.REJECTED):
      logger.info(f"Upload {upload_id} skipped: already finalized or not found.")
      return

    upload.workflow_status = WorkflowEnum.PROCESSING
    session.commit()

    ext = os.path.splitext(upload.file_original_name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
      temp_path = tmp.name
      s3.download_file('temporary', upload.temporary_minio_path, temp_path)
    
    validator = FileValidator()
    validation_result = validator.validate(
      local_path=temp_path,
      original_name=upload.file_original_name,
      declared_mime=upload.file_mime,
      file_size=upload.file_size
    )
    
    upload.processing_metadata['validation_result'] = validation_result
    upload.processing_metadata['pipeline_stage'] = 'validated'
    
    session.commit()
    logger.info(f"Validation completed successfully for upload {upload_id}")

  except FileValidationError as e:
    session.rollback()
    upload = session.get(UploadRequest, upload_id)
    if upload:
      upload.workflow_status = WorkflowEnum.REJECTED
      upload.rejection_reason = str(e)
      if upload and upload.temporary_minio_path:
        _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
      session.commit()
    logger.warning(f"Validation failed for upload {upload_id}: {e}")
  
  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "validate_file_task", getattr(job, "retries_left", None))
    raise
  
  finally:
    session.close()
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)

def extract_text_task(upload_id: int) -> None:
  """
  Скачивает файл из временного бакета, извлекает текст через Tika/PyMuPDF/Tesseract\n
  Сохраняет результат в processing_metadata\n
  Обновляет pipeline_stage
  """
  job = get_current_job()
  session = SyncSessionLocal()
  temp_path = None
  s3 = _get_sync_s3()
  
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status in (WorkflowEnum.ACCEPTED, WorkflowEnum.REJECTED):
      logger.info(f"Upload {upload_id} skipped: already finalized or not found.")
      return

    upload.processing_metadata['pipeline_stage'] = 'extracting_text'
    session.commit()

    ext = os.path.splitext(upload.file_original_name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
      temp_path = tmp.name
      s3.download_file('temporary', upload.temporary_minio_path, temp_path)

    result = extract_text(temp_path, upload.file_mime, upload.file_original_name)

    upload.processing_metadata['extracted_text'] = result['text']
    upload.processing_metadata['text_extraction'] = {
      "method": result['method'],
      "length": result['length'],
      "is_truncated": result['is_truncated']
    }
    upload.processing_metadata['pipeline_stage'] = 'text_extracted'
    
    session.commit()
    logger.info(f"Text extraction completed for upload {upload_id}")

  except TextExtractionError as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "extract_text_task", getattr(job, "retries_left", None))
    raise
  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "extract_text_task", getattr(job, "retries_left", None))
    raise
  finally:
    session.close()
    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)

def finalize_upload_task(upload_id: int) -> None:
  """
  Вычисляет risk_score, применяет пороги и переводит upload_requests в финальный статус: ACCEPTED / PENDING_REVIEW / REJECTED.
  """
  job = get_current_job()
  session = SyncSessionLocal()
  s3 = _get_sync_s3()
  
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status in (WorkflowEnum.ACCEPTED, WorkflowEnum.REJECTED):
      logger.info(f"Upload {upload_id} skipped: already finalized or not found.")
      return

    # Проверка идемпотентности: если score уже есть — пропускаем пересчёт
    if 'risk_score' not in upload.processing_metadata and 'risk_factors' in upload.processing_metadata:
      
      # Получаем возраст аккаунта автора
      author = session.get(User, upload.uploader_id)
      account_age_days = None
      if author and author.registration_date:
        reg_date = author.registration_date.replace(tzinfo=timezone.utc) if author.registration_date.tzinfo is None else author.registration_date
        account_age_days = (datetime.now(timezone.utc) - reg_date).days
    
      # Проверка на коллизию хеша
      existing_doc = session.execute(
        select(Document.id).where(Document.file_hash == upload.file_hash)
      ).scalar_one_or_none()
      upload.processing_metadata['hash_collision'] = existing_doc is not None

      # Расчёт risk_score
      analyzer = RiskAnalyzer()
      result = analyzer.calculate(upload, account_age_days or 999)  # 999 = старый аккаунт
      upload.processing_metadata['risk_score'] = result['score']
      upload.processing_metadata['risk_factors'] = result['factors']
      
      logger.info(f"Risk score calculated for upload {upload_id}: {result['score']}")
    else:
      logger.info(f"Risk score already calculated for upload {upload_id}")
    
    
    # Применение порогов и переход статуса (выполняется всегда, после гарантии наличия risk_score)
    risk_score = upload.processing_metadata.get('risk_score', 0)
    settings = get_settings()

    if risk_score > settings.RISK_THRESHOLD_REJECT:
      upload.workflow_status = WorkflowEnum.REJECTED
      upload.rejection_reason = f"High risk score: {risk_score}"
    elif risk_score > settings.RISK_THRESHOLD_REVIEW:
      upload.workflow_status = WorkflowEnum.PENDING_REVIEW
    else:
      upload.workflow_status = WorkflowEnum.ACCEPTED

    upload.processing_metadata['pipeline_stage'] = 'finalized'
    
    if upload.workflow_status == WorkflowEnum.REJECTED:
      if upload.temporary_minio_path:
        _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
    
    session.commit()
    logger.info(f"Pipeline finalized for upload {upload_id}. Status: {upload.workflow_status}")

  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "finalize_upload_task", getattr(job, "retries_left", None))
    raise
  finally:
    session.close()

def publish_document_task(upload_id: int) -> None:
  """
  Публикует документ в основном бакете и создаёт запись в таблице documents\n
  Запускается только при статусе ACCEPTED. Не блокирует pipeline
  """
  session = SyncSessionLocal()
  s3 = _get_sync_s3()
  temp_path_cleaned = False
  
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status != WorkflowEnum.ACCEPTED:
      return

    # Идемпотентность: проверяем, не опубликован ли файл уже
    existing = session.execute(
      select(Document).where(Document.file_hash == upload.file_hash)
    ).scalar_one_or_none()
    if existing:
      logger.info(f"Document already published for upload {upload_id}")
      if upload.temporary_minio_path:
        _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
      return

    dest_bucket = get_settings().MINIO_BUCKET or "documents"
    dest_key = f"documents/{upload.uploader_id}/{upload.file_hash}/{upload.file_original_name}"

    try:
      # Копирование из временного в основной бакет
      s3.copy_object(
        Bucket=dest_bucket,
        Key=dest_key,
        CopySource={"Bucket": "temporary", "Key": upload.temporary_minio_path}
      )
    except ClientError as e:
      code = e.response.get("Error", {}).get("Code", "Unknown")
      if code == "NoSuchKey":
        logger.error(f"Source file not found in temporary: {upload.temporary_minio_path}")
      elif code == "AccessDenied":
        logger.error(f"Access denied for MinIO copy operation")
      raise

    # Определение формата
    ext = upload.file_original_name.rsplit(".", 1)[-1].lower() if "." in upload.file_original_name else "unknown"
    fmt = ext if ext in ("pdf", "docx", "pptx", "txt", "md") else "unknown"

    doc = Document(
      title=upload.title,
      description=upload.description,
      uploader_id=upload.uploader_id,
      minio_bucket=dest_bucket,
      minio_object_path=dest_key,
      file_original_name=upload.file_original_name,
      file_mime=upload.file_mime,
      file_size=upload.file_size,
      file_hash=upload.file_hash,
      format=fmt,
      converted_to_pdf=False,
      visibility_status=VisibilityEnum.PUBLISHED,
      publish_date=datetime.now(timezone.utc)
    )
    session.add(doc)
    session.flush()

    upload.processing_metadata['published_document_id'] = doc.id
    upload.processing_metadata['pipeline_stage'] = 'published'
    session.commit()

    # Очистка временного файла после успешной публикации
    if upload.temporary_minio_path:
      _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
    temp_path_cleaned = True
    logger.info(f"Document {doc.id} published from upload {upload_id}")
  except IntegrityError:
    session.rollback()
    # Документ уже создан конкурентным воркером — это не ошибка
    logger.info(f"Document with hash {upload.file_hash} already exists (concurrent publish)")
    if not temp_path_cleaned and upload and upload.temporary_minio_path:
      _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
  
  except Exception as e:
    session.rollback()
    logger.error(f"Publication failed for upload {upload_id}: {e}")
    
    if upload and not temp_path_cleaned:
      _cleanup_temp_file_direct(s3, upload.temporary_minio_path)
    raise
  finally:
    session.close()

def convert_to_pdf_task(upload_id: int) -> None:
  """
  Опциональная конвертация в PDF\n
  Запускается только при ACCEPTED и поддерживаемом формате\n
  Не блокирует публикацию. Ошибки логируются, статус workflow не меняется
  """
  session = SyncSessionLocal()
  temp_path = None
  conv_job = None
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status != WorkflowEnum.ACCEPTED:
      return

    if not needs_conversion(upload.file_original_name):
      logger.info(f"Conversion skipped for upload {upload_id}: unsupported format")
      return

    # Создание/обновление записи задачи конвертации
    job_stmt = select(ConversionJob).where(
      ConversionJob.source_entity_id == upload_id,
      ConversionJob.target_format == "pdf"
    ).order_by(ConversionJob.id.desc()).limit(1)
    conv_job = session.execute(job_stmt).scalar_one_or_none()

    if not conv_job:
      conv_job = ConversionJob(
        source_entity_id=upload_id,
        original_format=upload.file_original_name.rsplit(".", 1)[-1].lower(),
        target_format="pdf",
        conversion_status=ConversionEnum.PENDING
      )
      session.add(conv_job)
      session.flush()

    conv_job.conversion_status = ConversionEnum.PROCESSING
    conv_job.started_at = datetime.now(timezone.utc)
    session.commit()

    # Скачивание оригинала во временный файл
    settings = get_settings()
    s3 = boto3.client("s3",
      endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
      aws_access_key_id=settings.MINIO_ACCESS_KEY,
      aws_secret_access_key=settings.MINIO_SECRET_KEY,
      verify=settings.VERIFY_TLS
    )

    ext = os.path.splitext(upload.file_original_name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
      temp_path = tmp.name
      s3.download_file("temporary", upload.temporary_minio_path, temp_path)

    # Конвертация
    pdf_bytes = convert_to_pdf_sync(temp_path)

    # Загрузка результата в основной бакет
    pdf_object_name = f"documents/{upload.uploader_id}/{upload.file_hash}/{upload.file_original_name.rsplit('.', 1)[0]}.pdf"
    s3.put_object(
      Bucket="documents",
      Key=pdf_object_name,
      Body=pdf_bytes,
      ContentType="application/pdf"
    )

    # Обновление статуса задачи
    conv_job.conversion_status = ConversionEnum.COMPLETED
    conv_job.completed_at = datetime.now(timezone.utc)
    conv_job.output_minio_path = pdf_object_name
    session.commit()

    # Обновление флага в таблице документов (если документ уже опубликован)
    session.execute(
      update(Document).where(Document.file_hash == upload.file_hash).values(converted_to_pdf=True)
    )
    session.commit()

    logger.info(f"PDF conversion completed for upload {upload_id} -> {pdf_object_name}")

  except Exception as e:
    session.rollback()
    if conv_job:
      conv_job.conversion_status = ConversionEnum.FAILED
      conv_job.completed_at = datetime.now(timezone.utc)
      conv_job.error_log = (conv_job.error_log or "") + f"\n[{datetime.now(timezone.utc).isoformat()}] Conversion failed: {str(e)}"
      session.commit()
    logger.error(f"PDF conversion failed for upload {upload_id}: {e}")
    # Не пробрасываем исключение, чтобы не менять workflow_status документа
  finally:
    session.close()
    if temp_path and os.path.exists(temp_path):
      os.remove(temp_path)