import logging
from datetime import timedelta

from common.policies import Refused

from . import models
from .constants import RunStep
from .context import BotContextBuilder
from .factory import BotFactory

logger = logging.getLogger(__name__)


class Step:
    name = None
    task = None
    timeout = None

    def __init__(self, factory=None):
        self.factory = factory or BotFactory()

    def execute(self, run):
        try:
            context = BotContextBuilder(run.member).build()
            run.save_snapshot(context)
            bot = self.factory.build(run.bot, context)
            self.apply(run, self.decide(bot, run))
        except Exception as error:
            models.Run.objects.fail(run, error)
            raise

    def decide(self, bot, run):
        raise NotImplementedError

    def apply(self, run, result):
        raise NotImplementedError


class DrawDecisionStep(Step):
    name = RunStep.DRAW_DECISION
    task = "bot.decide_draw"
    timeout = timedelta(minutes=2)

    def decide(self, bot, run):
        return bot.decide_draw()

    def apply(self, run, accepted):
        try:
            models.Run.objects.vote_on_draw(run, accepted)
        except Refused as refusal:
            logger.warning(
                "Skipping draw decision run %s: vote refused with %s",
                run.pk,
                refusal.decision.reason,
            )
            models.Run.objects.skip(run)


STEPS = {step.name: step for step in (DrawDecisionStep(),)}
