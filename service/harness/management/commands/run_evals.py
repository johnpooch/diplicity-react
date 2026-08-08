import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from inspect_ai import eval as inspect_eval

from dumbbot.evals import dumbbot_select_orders

from harness.recorder import record
from harness.tasks.select_orders.evals import select_orders

SELECT_ORDERS = "select_orders"
DUMBBOT = "dumbbot"

DUMBBOT_INSPECT_MODEL = "mockllm/model"


class Command(BaseCommand):
    help = "Run the harness evals and optionally record the run"

    def add_arguments(self, parser):
        parser.add_argument("--task", choices=(SELECT_ORDERS, DUMBBOT), default=SELECT_ORDERS)
        parser.add_argument("--model", default=f"anthropic/{settings.BOT_LLM_MODEL}")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--record", action="store_true")

    def handle(self, *args, **options):
        if options["record"] and options["limit"]:
            raise CommandError("--record cannot be combined with --limit: a partial run is not a baseline")

        if options["task"] == DUMBBOT:
            task, model, recorded_model = dumbbot_select_orders(), DUMBBOT_INSPECT_MODEL, DUMBBOT
        else:
            if not settings.BOT_ANTHROPIC_API_KEY:
                self.stdout.write("skip: BOT_ANTHROPIC_API_KEY is not set")
                return
            os.environ.setdefault("ANTHROPIC_API_KEY", settings.BOT_ANTHROPIC_API_KEY)
            task, model, recorded_model = select_orders(), options["model"], options["model"]

        log = inspect_eval(task, model=model, limit=options["limit"])[0]

        if not options["record"]:
            return
        self.stdout.write(f"recorded: {record(log, model=recorded_model)}")
