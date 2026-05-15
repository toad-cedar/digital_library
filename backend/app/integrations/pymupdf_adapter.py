import logging
import fitz


logger = logging.getLogger(__name__)

def extract_with_pymupdf(file_path: str) -> str:
  """
  Извлекает текстовый слой из PDF через PyMuPDF.
  Подходит для документов с нативным текстом.
  """
  doc = fitz.open(file_path)
  try:
    text_parts = [page.get_text() for page in doc]
    return "".join(text_parts)
  finally:
    doc.close()