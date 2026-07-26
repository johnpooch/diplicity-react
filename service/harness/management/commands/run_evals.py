from django.conf import settings
from django.core.management.base import BaseCommand

from harness.evals import TASK_PACKAGES, discover


class Command(BaseCommand):
    help = "Run the harness evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("task", nargs="?", choices=sorted(TASK_PACKAGES))

    def handle(self, *args, **options):
        if not settings.BOT_ANTHROPIC_API_KEY:
            self.stdout.write("skip: BOT_ANTHROPIC_API_KEY is not set")
            return
        for eval_spec in discover(options["task"]):
            eval_spec.run(self.stdout)
