import os

from django.conf import settings
from django.core.management.base import BaseCommand
from inspect_ai import eval as inspect_eval

from select_orders.evals import select_orders


class Command(BaseCommand):
    help = "Run the select_orders evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("--model", default=settings.EVALS_MODEL)
        parser.add_argument("--limit", type=int, default=None)

    def handle(self, *args, **options):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.stdout.write("skip: ANTHROPIC_API_KEY is not set")
            return
        inspect_eval(select_orders(), model=options["model"], limit=options["limit"])
