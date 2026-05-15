import logging
import os
import gc
import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image


logger = logging.getLogger(__name__)

OCR_DPI = 150 # Оптимальный баланс качество/память
MAX_OCR_PAGES = 100 # Защита от зависания на многостраничных документах

def extract_with_tesseract(file_path: str) -> str:
  """
  Распознает текст в сканах PDF и изображениях через Tesseract OCR.
  Обрабатывает PDF постранично для предотвращения OOM.
  Требует tesseract-ocr и poppler-utils.
  """
  ext = os.path.splitext(file_path)[1].lower()
  texts = []

  try:
    if ext == '.pdf':
      info = pdfinfo_from_path(file_path)
      total_pages = min(info.get("Pages", 0), MAX_OCR_PAGES)
      
      for page_num in range(1, total_pages + 1):
        images = convert_from_path(
          file_path,
          dpi=OCR_DPI,
          first_page=page_num,
          last_page=page_num,
          thread_count=1  # Последовательная отрисовка
        )
        if not images:
          continue

        img = images[0]
        texts.append(pytesseract.image_to_string(img, lang='rus+eng'))

        # Освобождение памяти после каждой страницы
        img.close()
        del images
        gc.collect()
    else:
      images = Image.open(file_path)
      try:
        texts.append(pytesseract.image_to_string(img, lang='rus+eng'))
      finally:
        img.close()
        
    return " ".join(texts)
  except Exception as e:
    raise RuntimeError(f"Tesseract OCR failed: {e}")