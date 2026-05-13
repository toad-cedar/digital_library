import time
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from app.config.settings import get_settings
from app.core.exceptions import IntegrationConnectionError, IntegrationTimeoutError, IntegrationServiceError

def get_minio_client() -> boto3.client:
  settings = get_settings()
  return boto3.client(
    's3',
    endpoint_url=settings.MINIO_ENDPOINT, 
    aws_access_key_id=settings.MINIO_ACCESS_KEY, 
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    region_name=settings.MINIO_REGION,
    use_ssl=settings.MINIO_SECURE,
    verify=settings.VERIFY_TLS,
    config=Config(
      signature_version='s3v4',
      retries={'max_attempts': 3, 'mode': 'standard'},
      connect_timeout=5,
      read_timeout=10,
      max_pool_connections=10
    )
  )

def minio_safe_call(func, *args, max_retries: int = 3, **kwargs):
  last_error = None
  
  for attempt in range(max_retries):
    try:
      return func(*args, **kwargs)
    except (ConnectionError, BotoCoreError) as e:
      last_error = e
      if attempt == max_retries - 1:
        if "timeout" in str(e).lower():
          raise IntegrationTimeoutError(f"MinIO timeout: {e}") from e
        raise IntegrationConnectionError(f"MinIO connection failed: {e}") from e
      time.sleep(2 ** attempt)
    except ClientError as e:
      raise IntegrationServiceError(
        f"MinIO API error {e.response['Error']['Code']}: {e.response['Error']['Message']}"
      ) from e
  raise IntegrationConnectionError("MinIO call failed after retries") from last_error