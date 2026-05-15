import asyncio
import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError, ConnectionError
from app.config.settings import get_settings
from app.core.exceptions import IntegrationConnectionError, IntegrationTimeoutError, IntegrationServiceError


async def async_minio_safe_call(func, *args, max_retries: int = 3, **kwargs):
  settings = get_settings()
  config = Config(
    signature_version='s3v4',
    retries={'max_attempts': 2, 'mode': 'standard'},
    connect_timeout=5,
    read_timeout=10,
    max_pool_connections=10
  )
  session = aioboto3.Session()

  last_error = None
  for attempt in range(max_retries):
    try:
        async with session.client(
          's3',
          endpoint_url=f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}",
          aws_access_key_id=settings.MINIO_ACCESS_KEY,
          aws_secret_access_key=settings.MINIO_SECRET_KEY,
          region_name=settings.MINIO_REGION,
          use_ssl=settings.MINIO_SECURE,
          verify=settings.VERIFY_TLS,
          config=config
        ) as client:
          return await func(client, *args, **kwargs)
    except (ConnectTimeoutError, ReadTimeoutError) as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationTimeoutError(f"MinIO timeout: {e}") from e
      await asyncio.sleep(2 ** attempt)
    except ConnectionError as e:
      last_error = e
      if attempt == max_retries - 1:
        raise IntegrationConnectionError(f"MinIO connection failed: {e}") from e
      await asyncio.sleep(2 ** attempt)
    except ClientError as e:
      raise IntegrationServiceError(
        f"MinIO API error {e.response['Error']['Code']}: {e.response['Error']['Message']}"
      ) from e
  raise IntegrationConnectionError("MinIO call failed after retries") from last_error