from procrastinate.contrib.django import app

from .constants import COORDINATE_TASK
from .coordinator import Coordinator
from .models import Run
from .steps import STEPS, DrawDecisionStep


@app.periodic(cron="* * * * *")
@app.task(name=COORDINATE_TASK, lock=COORDINATE_TASK)
def coordinate(timestamp=None):
    Coordinator().tick()


@app.task(name=DrawDecisionStep.task)
def decide_draw(pk):
    STEPS[DrawDecisionStep.name].execute(Run.objects.get(pk=pk))
