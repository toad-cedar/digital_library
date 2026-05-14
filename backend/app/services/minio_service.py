from app.integrations.minio_client import async_minio_safe_call
import logging


logger = logging.getLogger(__name__)

class MinioService:
  async def upload_file(self, bucket: str, object_key: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> None:
    await async_minio_safe_call(
      lambda client: client.put_object(
        Bucket=bucket, Key=object_key, Body=file_bytes, ContentType=content_type
      )
    )

  async def get_presigned_url(self, bucket: str, object_key: str, expires_seconds: int = 3600) -> str:
    return await async_minio_safe_call(
      lambda client: client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expires_seconds,
      )
    )

  async def delete_file(self, bucket: str, object_key: str) -> None:
    await async_minio_safe_call(
      lambda client: client.delete_object(Bucket=bucket, Key=object_key)
    )

  async def copy_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str) -> None:
    await async_minio_safe_call(
      lambda client: client.copy_object(
        Bucket=dest_bucket,
        Key=dest_key,
        CopySource={"Bucket": source_bucket, "Key": source_key},
      )
    )