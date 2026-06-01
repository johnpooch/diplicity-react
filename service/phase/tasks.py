import logging

from procrastinate.contrib.django import app

from phase.models import Phase

logger = logging.getLogger(__name__)


@app.task(name="phase.resolve_phase", retry=3)
def resolve_phase(phase_id: int):
    logger.info(f"Running resolve_phase task for phase {phase_id}")
    Phase.objects.resolve_if_due(phase_id)


@app.periodic(cron="* * * * *")
@app.task(name="phase.sweep_due_phases")
def sweep_due_phases(timestamp: int):
    logger.info(f"Running sweep_due_phases task (scheduled for {timestamp})")
    Phase.objects.sweep_due_phases()
