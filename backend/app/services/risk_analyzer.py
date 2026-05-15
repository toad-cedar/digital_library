from datetime import timezone
from typing import Dict, Any
from app.config.settings import get_settings
from app.models.document_models import UploadRequest

class RiskAnalyzer:
  """Расчёт risk_score на основе факторов загрузки и метаданных"""

  def __init__(self):
    self.settings = get_settings()
    self.weights = getattr(self.settings, 'RISK_WEIGHTS', {})
    self.known_mimes = {
      'application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain', 'text/markdown', 'image/jpeg', 'image/png', 'image/tiff'
    }

  def calculate(self, upload: UploadRequest, author_account_age_days: int) -> Dict[str, Any]:
    """
    Вычисляет risk_score и детализацию факторов\n
    Возвращает dict с 'score' и 'factors' для сохранения в processing_metadata
    """
    score = 0
    factors = {}

    # Фактор 1: новый аккаунт
    if author_account_age_days < 7:
      weight = self.weights.get('new_account_days', 20)
      score += weight
      factors['new_account'] = {'weight': weight, 'value': author_account_age_days}

    # Фактор 2: неизвестный MIME
    if upload.file_mime not in self.known_mimes:
      weight = self.weights.get('unknown_mime', 30)
      score += weight
      factors['unknown_mime'] = {'weight': weight, 'value': upload.file_mime}

    # Фактор 3: отсутствие OCR-текста для файлов, где он ожидается
    ext = upload.file_original_name.rsplit('.', 1)[-1].lower() if upload.file_original_name else ''
    if ext in ('pdf', 'jpg', 'jpeg', 'png', 'tiff'):
      ocr_found = upload.processing_metadata.get('text_extraction', {}).get('method') == 'tesseract_ocr'
      has_native_text = upload.processing_metadata.get('text_extraction', {}).get('method') == 'pymupdf'
      if not ocr_found and not has_native_text:
        weight = self.weights.get('no_ocr_text', 15)
        score += weight
        factors['no_ocr_text'] = {'weight': weight}

    # Фактор 4: совпадение хеша (проверяется на уровне репозитория)
    # Значение передаётся извне, так как требует БД-запроса
    if upload.processing_metadata.get('hash_collision', False):
      weight = self.weights.get('hash_collision', 50)
      score += weight
      factors['hash_collision'] = {'weight': weight}

    # Фактор 5: большой файл
    if upload.file_size > 50 * 1024 * 1024:  # 50 МБ
      weight = self.weights.get('large_file', 10)
      score += weight
      factors['large_file'] = {'weight': weight, 'size_mb': upload.file_size / (1024*1024)}

    # Фактор 6: ночная загрузка
    upload_time = upload.created_at.replace(tzinfo=timezone.utc) if upload.created_at.tzinfo is None else upload.created_at
    if 2 <= upload_time.hour < 6:
      weight = self.weights.get('night_upload', 5)
      score += weight
      factors['night_upload'] = {'weight': weight, 'hour': upload_time.hour}

    # Ограничение сверху
    score = min(score, 100)

    return {
      'score': score,
      'factors': factors,
      'thresholds': {
        'reject': self.settings.RISK_THRESHOLD_REJECT,
        'review': self.settings.RISK_THRESHOLD_REVIEW
      }
    }