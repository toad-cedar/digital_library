import redis
from redis.exceptions import TimeoutError, ConnectionError, ResponseError
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call

def get_redis_client():
  settings = get_settings()
  return redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=10,
    retry_on_timeout=True,
    max_connections=20
  )

def redis_safe_call(func, *args, max_retries: int = 3, **kwargs):
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(TimeoutError,),
    connection_exc=(ConnectionError,),
    service_exc=(ResponseError,),
    **kwargs
  )