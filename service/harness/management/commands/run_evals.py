import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from inspect_ai import eval

from harness.evals import TASK_PACKAGES, discover
from harness.evals.select_orders.capitals import capitals
from harness.evals.select_orders.select_orders_structure import select_orders_structure, select_orders_coherence, select_orders_tactics


class Command(BaseCommand):
    help = "Run the harness evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("task", nargs="?", choices=sorted(TASK_PACKAGES))

    def handle(self, *args, **options):
        if not settings.BOT_ANTHROPIC_API_KEY:
            self.stdout.write("skip: BOT_ANTHROPIC_API_KEY is not set")
            return

        home_dir = Path("/tmp/inspect-ai-home")
        data_dir = Path("/tmp/inspect-ai-data")
        home_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        os.environ.setdefault("HOME", str(home_dir))
        os.environ.setdefault("XDG_DATA_HOME", str(data_dir))

        eval(select_orders_structure(), model="anthropic/claude-haiku-4-5", epochs=10)
        eval(select_orders_coherence(), model="anthropic/claude-haiku-4-5", epochs=10)
        eval(select_orders_tactics(), model="anthropic/claude-haiku-4-5", epochs=1)
