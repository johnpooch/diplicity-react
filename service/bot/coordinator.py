from .models import Run
from .steps import STEPS


class Coordinator:
    def tick(self):
        for run in Run.objects.stale_phase():
            Run.objects.skip(run)
        for run in Run.objects.overdue(STEPS):
            Run.objects.time_out(run)
        for run in Run.objects.ready():
            Run.objects.start(run)
