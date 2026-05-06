from botocore.exceptions import ClientError
from app.integrations.minio_client import minio_client
import logging

logger = logging.getLogger(__name__)


class MinioService:
  def __init__(self):
      self.client = minio_client

  async def put_object(
      self, bucket_name: str, object_name: str, data: bytes, length: int, content_type: str = "application/octet-stream"
  ):
    """Загружает объект в бакет."""
    try:
      # Boto3 sync client внутри async функции.
      # Это блокирует event loop. Для высоконагруженных приложений использовать aiofiles и потоковую передачу.
      self.client.put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=data,
        ContentLength=length,
        ContentType=content_type,
      )
    except ClientError as e:
      logger.error(f"MinIO put_object error: {e}")
      raise e

  async def get_object(self, bucket_name: str, object_name: str) -> bytes:
    """Получает содержимое объекта."""
    try:
      response = self.client.get_object(Bucket=bucket_name, Key=object_name)
      return response["Body"].read()
    except ClientError as e:
      logger.error(f"MinIO get_object error: {e}")
      raise e

  async def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = 3600) -> str:
    """Генерирует предварительно подписанный URL для доступа к объекту."""
    try:
      presigned_url = self.client.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': object_name},
        ExpiresIn=expires,
      )
      return presigned_url
    except ClientError as e:
      logger.error(f"MinIO generate_presigned_url error: {e}")
      raise e

  async def delete_object(self, bucket_name: str, object_name: str):
    """Удаляет объект из бакета."""
    try:
      self.client.delete_object(Bucket=bucket_name, Key=object_name)
    except ClientError as e:
      logger.error(f"MinIO delete_object error: {e}")
      raise e

  async def bucket_exists(self, bucket_name: str) -> bool:
    """Проверяет, существует ли бакет."""
    try:
      self.client.head_bucket(Bucket=bucket_name)
      return True
    except ClientError as e:
      if e.response['Error']['Code'] == '404':
        logger.error(f"MinIO bucket ({bucket_name}) does not exist")
        return False  # бакет не существует
      else:
        logger.error(f"MinIO head_bucket error: {e}")
        raise e
