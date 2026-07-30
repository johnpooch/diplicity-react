import os

from django.conf import settings
from django.core.management.base import BaseCommand
from inspect_ai import eval as inspect_eval

from harness.tasks.select_orders.evals import select_orders


class Command(BaseCommand):
    help = "Run the harness evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("--model", default=f"anthropic/{settings.BOT_LLM_MODEL}")
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        if not settings.BOT_ANTHROPIC_API_KEY:
            self.stdout.write("skip: BOT_ANTHROPIC_API_KEY is not set")
            return
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.BOT_ANTHROPIC_API_KEY)
        inspect_eval(select_orders(), model=options["model"], limit=options["limit"])
