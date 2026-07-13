from django.core.management.base import BaseCommand

from harness.evals.runner import CASES, run


class Command(BaseCommand):
    help = "Run the harness evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("task", nargs="?", choices=sorted(CASES))

    def handle(self, *args, **options):
        run(self.stdout, task_name=options["task"])
