import os
import logging
import fitz
from app.integrations.pymupdf_adapter import extract_with_pymupdf
from app.integrations.tika_adapter import extract_with_tika
from app.integrations.tesseract_adapter import extract_with_tesseract


logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 500_000  # Лимит символов для сохранения в JSONB

class TextExtractionError(Exception):
  """Ошибка извлечения текста, требующая повторной попытки или ручной проверки"""
  pass

def _has_text_layer(file_path: str) -> bool:
  """Проверяет наличие нативного текстового слоя в PDF через PyMuPDF"""
  doc = None
  try:
    doc = fitz.open(file_path)
    for page in doc:
      if page.get_text("words"): # get_text возвращает список кортежей. Пустой список = скан/изображение
        return True
    return False
  except Exception as e:
    logger.warning(f"fitz catched an exception: {e}")
    return False
  finally:
    if doc:
      doc.close()

def extract_text(file_path: str, mime: str, filename: str) -> dict:
  """
  Определяет тип файла и маршрутизирует к нужному адаптеру\n
  Реализует fallback: если PDF не содержит текстовый слой, переключается на OCR\n
  Возвращает dict с текстом, метаданными и флагом обрезки
  """
  ext = os.path.splitext(filename)[1].lower()
  text = ""
  method = ""

  try:
    if ext in ('.docx', '.pptx', '.txt', '.rtf'):
      method = "tika"
      text = extract_with_tika(file_path)
    elif ext == '.pdf':
      if _has_text_layer(file_path):
        method = "pymupdf"
        text = extract_with_pymupdf(file_path)
      else:
        logger.info("PDF lacks native text layer, switching to Tesseract OCR")
        method = "tesseract_ocr"
        text = extract_with_tesseract(file_path)
    elif mime.startswith(('image/', 'application/x-tiff')):
      method = "tesseract_ocr"
      text = extract_with_tesseract(file_path)
    else:
      raise TextExtractionError(f"Unsupported format for extraction: {mime}")

    is_truncated = len(text) > MAX_TEXT_CHARS
    if is_truncated:
      text = text[:MAX_TEXT_CHARS]

    return {
      "text": text,
      "is_truncated": is_truncated,
      "method": method,
      "length": len(text)
    }
  except Exception as e:
    raise TextExtractionError(f"Extraction pipeline failed ({method}): {e}")