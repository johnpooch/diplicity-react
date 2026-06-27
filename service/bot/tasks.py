import logging

from django.apps import apps
from procrastinate.contrib.django import app

from bot.play import play_bot_turn

logger = logging.getLogger(__name__)


@app.task(name="bot.play_phase", retry=3)
def play_phase(phase_id: int):
    Phase = apps.get_model("phase", "Phase")
    phase = Phase.objects.filter(pk=phase_id).select_related("game", "variant").first()
    if phase is None:
        logger.info(f"Phase {phase_id} no longer exists; skipping bot turn")
        return
    play_bot_turn(phase)
