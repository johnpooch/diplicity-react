import logging

from procrastinate.contrib.django import app

from common.constants import ResolutionJob
from phase.models import Phase

logger = logging.getLogger(__name__)


@app.task(name=ResolutionJob.TASK_NAME, retry=3)
def resolve_phase(phase_id: int):
    logger.info(f"Running resolve_phase task for phase {phase_id}")
    Phase.objects.resolve_if_due(phase_id)


@app.periodic(cron="* * * * *")
@app.task(name="phase.send_deadline_warnings")
def send_deadline_warnings(timestamp: int):
    logger.info(f"Running send_deadline_warnings task (scheduled for {timestamp})")
    Phase.objects.send_deadline_warnings()
