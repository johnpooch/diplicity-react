import logging

from procrastinate.contrib.django import app

logger = logging.getLogger(__name__)

JOB_RETENTION_HOURS = 168
STALLED_WORKER_SECONDS = 60


@app.periodic(cron="*/5 * * * *")
@app.task
def heartbeat(timestamp: int):
    logger.info(f"Procrastinate worker heartbeat (scheduled for {timestamp})")


@app.periodic(cron="30 3 * * *")
@app.task(name="health.purge_old_jobs")
async def purge_old_jobs(timestamp: int):
    logger.info(
        f"Purging Procrastinate jobs finished more than {JOB_RETENTION_HOURS}h ago"
    )
    await app.job_manager.delete_old_jobs(
        nb_hours=JOB_RETENTION_HOURS,
        include_cancelled=True,
    )


@app.periodic(cron="*/5 * * * *")
@app.task(name="health.retry_stalled_jobs")
async def retry_stalled_jobs(timestamp: int):
    stalled_jobs = await app.job_manager.get_stalled_jobs(
        seconds_since_heartbeat=STALLED_WORKER_SECONDS
    )
    for job in stalled_jobs:
        logger.warning(
            "Retrying stalled Procrastinate job %s (%s)", job.id, job.task_name
        )
        await app.job_manager.retry_job(job)
