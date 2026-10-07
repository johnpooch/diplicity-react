import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from inspect_ai import eval as inspect_eval

from select_orders.evals import select_orders
from select_orders.exceptions import FixtureError


class Command(BaseCommand):
    help = "Run the select_orders evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("--model", default=settings.EVALS_MODEL)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--eval-set", default=settings.EVALS_EVAL_SET)
        parser.add_argument("--epochs", type=int, default=1, help="model calls per fixture; each one is billed")

    def handle(self, *args, **options):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.stdout.write("skip: ANTHROPIC_API_KEY is not set")
            return
        try:
            task = select_orders(options["eval_set"])
        except FixtureError as e:
            raise CommandError(str(e)) from e
        inspect_eval(
            task,
            model=options["model"],
            limit=options["limit"],
            epochs=options["epochs"],
            log_dir=str(settings.EVALS_LOGS_DIR),
        )
