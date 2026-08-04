"""arq worker entry point.

Run with: ``arq src.worker.main.WorkerSettings``
"""

from arq.connections import RedisSettings

from src.web.config import get_settings
from src.worker.jobs import run_simulation


class WorkerSettings:
    functions = [run_simulation]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1
    job_timeout = 3600
