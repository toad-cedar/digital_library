import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.config.settings import get_settings

def get_minio_client():
  client = boto3.client(
    's3',
    endpoint_url=get_settings().MINIO_ENDPOINT, 
    aws_access_key_id=get_settings().MINIO_ACCESS_KEY, 
    aws_secret_access_key=get_settings().MINIO_SECRET_KEY,
    region_name=get_settings().MINIO_REGION,
    use_ssl=get_settings().MINIO_SECURE,
    verify=False,
    config=Config(signature_version='s3v4')
  )
  
  return client

minio_client = get_minio_client()