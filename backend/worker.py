import logging
import sys
from rq import Worker, Queue
from redis import Redis
from app.config.settings import get_settings


logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
  handlers=[logging.StreamHandler(sys.stdout)]
)

def start_worker() -> None:
  settings = get_settings()
  conn = Redis.from_url(settings.get_redis_url, decode_responses=True)
  queues = [
    Queue('default', connection=conn),
    Queue('heavy_processing', connection=conn)
  ]
  
  logger = logging.getLogger("rq.worker")
  worker = Worker(queues, connection=conn, job_monitoring_interval=5)
  logger.info("Starting RQ workers for queues: %s", [q.name for q in queues])
  worker.work(burst=False)

if __name__ == "__main__":
  start_worker()