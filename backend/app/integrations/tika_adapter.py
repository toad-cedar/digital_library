import urllib.request
import urllib.error
import logging
from app.config.settings import get_settings


logger = logging.getLogger(__name__)

def extract_with_tika(file_path: str) -> str:
  """
  Извлекает текст из .docx, .pptx, .txt через REST API Tika Server
  """
  settings = get_settings()
  url = f"{settings.TIKA_URL}/tika"
  timeout = settings.TIKA_TIMEOUT
  
  try:
    with open(file_path, "rb") as f:
      req = urllib.request.Request(url, data=f, method="PUT")
      with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8")
  except urllib.error.URLError as e:
    raise RuntimeError(f"Tika connection error: {e.reason}")
  except urllib.error.HTTPError as e:
    raise RuntimeError(f"Tika HTTP error {e.code}: {e.read().decode()}")
  except TimeoutError:
    raise RuntimeError("Tika extraction timed out")
  except FileNotFoundError:
    raise RuntimeError(f"File not found: {file_path}")