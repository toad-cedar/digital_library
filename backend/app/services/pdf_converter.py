import logging
import httpx

from app.integrations.conversion_adapter import get_conversion_client


logger = logging.getLogger(__name__)
CONVERSION_FORMATS = {"docx", "pptx", "txt", "md"}

def needs_conversion(filename: str) -> bool:
  """Проверяет, требуется ли конвертация по расширению файла"""
  ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
  return ext in CONVERSION_FORMATS

def convert_to_pdf_sync(file_path: str) -> bytes:
  """Отправляет файл во внешний сервис конвертации и возвращает PDF bytes."""
  try:
    with httpx.Client(base_url=get_conversion_client().base_url, timeout=60.0, verify=True) as client:
      with open(file_path, "rb") as f:
        resp = client.post("/convert", files={"file": f})
        resp.raise_for_status()
        return resp.content
  except httpx.HTTPStatusError as e:
    raise RuntimeError(f"Conversion service HTTP error: {e.response.status_code} {e.response.text}")
  except Exception as e:
    raise RuntimeError(f"Conversion request failed: {e}")