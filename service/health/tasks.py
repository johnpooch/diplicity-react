import logging

from procrastinate.contrib.django import app

logger = logging.getLogger(__name__)

JOB_RETENTION_HOURS = 168


@app.periodic(cron="*/5 * * * *")
@app.task
def heartbeat(timestamp: int):
    logger.info(f"Procrastinate worker heartbeat (scheduled for {timestamp})")


@app.periodic(cron="30 3 * * *")
@app.task(name="health.purge_old_jobs")
async def purge_old_jobs(timestamp: int):
    logger.info(f"Purging Procrastinate jobs finished more than {JOB_RETENTION_HOURS}h ago")
    await app.job_manager.delete_old_jobs(
        nb_hours=JOB_RETENTION_HOURS,
        include_cancelled=True,
    )
