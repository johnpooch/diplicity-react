import logging

from procrastinate.contrib.django import app

logger = logging.getLogger(__name__)


@app.periodic(cron="*/5 * * * *")
@app.task
def heartbeat(timestamp: int):
    logger.info(f"Procrastinate worker heartbeat (scheduled for {timestamp})")
