from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from select_orders.evals import PROMPTS_DIR, fixture_to_sample, select_fixtures
from select_orders.exceptions import FixtureError


class Command(BaseCommand):
    help = "Write a fixture's current system and user prompts to files to edit and pass to run_evals"

    def add_arguments(self, parser):
        parser.add_argument("--fixture", required=True)
        parser.add_argument("--eval-set", default=settings.EVALS_EVAL_SET)
        parser.add_argument(
            "--out",
            default=None,
            help="directory to write to; defaults to prompts/<fixture>",
        )

    def handle(self, *args, **options):
        try:
            [fixture] = select_fixtures(options["eval_set"], options["fixture"])
        except FixtureError as e:
            raise CommandError(str(e)) from e
        out = Path(options["out"]) if options["out"] else PROMPTS_DIR / fixture["id"]
        system, user = fixture_to_sample(fixture).input
        files = {out / "system.txt": system.text, out / "user.txt": user.text}
        existing = [str(path) for path in files if path.exists()]
        if existing:
            raise CommandError(f"refusing to overwrite {existing}")
        out.mkdir(parents=True, exist_ok=True)
        for path, text in files.items():
            path.write_text(text)
            self.stdout.write(f"wrote {path}")
