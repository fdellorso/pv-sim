"""arq worker entry point.

Run with: ``arq src.worker.main.WorkerSettings``
"""

import logging

from arq.connections import RedisSettings

from src.web.config import get_settings
from src.web.database import async_session, engine
from src.worker.jobs import run_optimization, run_simulation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def on_startup(ctx: dict) -> None:
    ctx["db_session"] = async_session


async def on_shutdown(ctx: dict) -> None:
    await engine.dispose()


class WorkerSettings:
    functions = [run_simulation, run_optimization]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 1
    job_timeout = 3600
    on_startup = on_startup
    on_shutdown = on_shutdown
