from redis import Redis
from rq import Queue
from app.config.settings import get_settings

settings = get_settings()
redis_conn = Redis.from_url(settings.get_redis_url, decode_responses=True)

default_queue = Queue('default', connection=redis_conn)
heavy_queue = Queue('heavy_processing', connection=redis_conn)