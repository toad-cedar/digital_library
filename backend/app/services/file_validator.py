import mimetypes
import logging
import magic
import os

from app.config.settings import get_settings


logger = logging.getLogger(__name__)

class FileValidationError(Exception):
  """Ошибка бизнес-валидации файла (не запускает retry RQ)"""
  pass

class FileValidator:
  """Проверяет размер, magic bytes, MIME-тип и соответствие расширения"""

  def __init__(self):
    self.settings = get_settings()
    self.max_size = getattr(self.settings, 'MAX_UPLOAD_SIZE', 100 * 1024 * 1024)
    self.allowed_mimes = {
      'application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain', 'text/markdown', 'image/jpeg', 'image/png', 'image/tiff'
    }

  def validate(self, local_path: str, original_name: str, declared_mime: str, file_size: int) -> dict:
    """
    Выполняет полную валидацию файла\n
    Возвращает dict с результатами проверки или raises FileValidationError
    """
    self._check_size(file_size)
    actual_mime = self._check_magic(local_path)
    ext = self._check_extension(original_name, actual_mime)
    self._check_mime_match(actual_mime, declared_mime)
    return {"actual_mime": actual_mime, "extension": ext, "size_valid": True}

  def _check_size(self, size: int) -> None:
    """Проверяет, не превышает ли файл лимит"""
    if size > self.max_size:
      raise FileValidationError(f"File size {size} exceeds limit {self.max_size} bytes.")

  def _check_magic(self, path: str) -> str:
    """Определяет реальный MIME-тип по сигнатуре файла"""
    mime = magic.from_file(path, mime=True)
    if mime not in self.allowed_mimes:
      raise FileValidationError(f"Unsupported file type: {mime}")
    return mime

  def _check_extension(self, name: str, mime: str) -> str:
    """Сверяет расширение с ожидаемым MIME-типом"""
    ext = os.path.splitext(name)[1].lower()
    expected_mime, _ = mimetypes.guess_type(name)
    if expected_mime and expected_mime != mime:
      raise FileValidationError(f"Extension {ext} does not match detected MIME {mime}.")
    return ext

  def _check_mime_match(self, actual: str, declared: str) -> None:
    """Сравнивает определённый MIME с заявленным при загрузке"""
    if actual != declared:
      raise FileValidationError(f"Declared MIME '{declared}' differs from actual '{actual}'.")