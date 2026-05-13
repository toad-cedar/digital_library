import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectionError, ConnectTimeoutError, ReadTimeoutError
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call


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
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(ConnectTimeoutError, ReadTimeoutError),
    connection_exc=(ConnectionError,),
    service_exc=(ClientError,),
    **kwargs
  )