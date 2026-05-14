import logging
import traceback
from datetime import datetime, timezone
from rq import get_current_job
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.sync_db import SyncSessionLocal
from app.models.document_models import UploadRequest
from app.models.processing_models import ConversionJob
from app.config.database import WorkflowEnum, ConversionEnum


logger = logging.getLogger(__name__)

def _update_job_error(session: Session, upload_id: int, error: Exception, context: str, retries_left: int) -> None:
  """Записывает ошибку, инкрементирует retry_count и обновляет статус в conversion_jobs"""
  stmt = select(ConversionJob).where(
    ConversionJob.source_entity_id == upload_id,
    ConversionJob.conversion_status.in_([ConversionEnum.PENDING, ConversionEnum.PROCESSING, ConversionEnum.RETRYING])
  ).order_by(ConversionJob.id.desc()).limit(1)
  job_record = session.execute(stmt).scalar_one_or_none()

  if not job_record:
    job_record = ConversionJob(source_entity_id=upload_id, conversion_status=ConversionEnum.PENDING)
    session.add(job_record)
    session.flush()

  max_retries = 3
  current_left = retries_left if retries_left is not None else 0
  job_record.retry_count = max(job_record.retry_count, max_retries - current_left)
  
  timestamp = datetime.now(timezone.utc).isoformat()
  job_record.error_log = (job_record.error_log or "") + f"\n[{timestamp}] {context}: {str(error)}\n{traceback.format_exc()}"

  if job_record.retry_count >= 3:
    job_record.conversion_status = ConversionEnum.FAILED
    upload = session.get(UploadRequest, upload_id)
    if upload:
      upload.workflow_status = WorkflowEnum.REJECTED
      upload.rejection_reason = f"Pipeline failed after retries: {context}"
  else:
    job_record.conversion_status = ConversionEnum.RETRYING
  
  session.commit()

def validate_file_task(upload_id: int) -> None:
  job = get_current_job()
  session = SyncSessionLocal()
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload or upload.workflow_status in (WorkflowEnum.ACCEPTED, WorkflowEnum.REJECTED):
      logger.info(f"Upload {upload_id} skipped: already finalized or not found.")
      return

    upload.workflow_status = WorkflowEnum.PROCESSING
    session.commit()

    # TODO: валидация magic bytes, MIME, размера, расширения
    logger.info(f"Validation completed for upload {upload_id}")

  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "validate_file_task", getattr(job, "retries_left", None))
    raise
  finally:
    session.close()

def extract_text_task(upload_id: int) -> None:
  job = get_current_job()
  session = SyncSessionLocal()
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload:
      return

    # TODO: Apache Tika / PyMuPDF / Tesseract
    # ! ocr_result = extract_text(upload.temporary_minio_path, upload.file_mime)
    # ! upload.processing_metadata['ocr_text_found'] = bool(ocr_result)
    # ! session.commit()

    logger.info(f"Text extraction completed for upload {upload_id}")

  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "extract_text_task", getattr(job, "retries_left", None))
    raise
  finally:
    session.close()

def finalize_upload_task(upload_id: int) -> None:
  job = get_current_job()
  session = SyncSessionLocal()
  try:
    upload = session.get(UploadRequest, upload_id)
    if not upload:
      return

    # TODO, заменить на вызов risk_analyzer.calculate()

    risk_score = upload.processing_metadata.get('risk_score', 0)

    if risk_score > 80:
      upload.workflow_status = WorkflowEnum.REJECTED
      upload.rejection_reason = "High risk score"
    elif risk_score > 30:
      upload.workflow_status = WorkflowEnum.PENDING_REVIEW
    else:
      upload.workflow_status = WorkflowEnum.ACCEPTED

    session.commit()
    logger.info(f"Pipeline finalized for upload {upload_id}. Status: {upload.workflow_status}")

  except Exception as e:
    session.rollback()
    _update_job_error(session, upload_id, e, "finalize_upload_task", getattr(job, "retries_left", None))
    raise
  finally:
    session.close()