import os

from arq.connections import RedisSettings


async def noop(ctx: dict) -> None:
    """Placeholder — будет заменён реальными задачами."""


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://redis:6379")
    )
    functions = [noop]
    max_jobs = 10
    job_timeout = 300
