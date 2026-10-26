from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from prompt_builder.variants import VARIANTS
from select_orders.context import fixture_to_context
from select_orders.evals import PROMPTS_DIR, fixture_to_sample, select_fixtures
from select_orders.exceptions import FixtureError, PromptError


class Command(BaseCommand):
    help = "Write each prompt variant's user prompt for every fixture, to pass to run_evals with --user-variant"

    def add_arguments(self, parser):
        parser.add_argument("--eval-set", default=settings.EVALS_EVAL_SET)
        parser.add_argument(
            "--fixture", default=None, help="build only this fixture of the eval set"
        )
        parser.add_argument(
            "--variant",
            action="append",
            choices=sorted(VARIANTS),
            help="build only these variants",
        )
        parser.add_argument(
            "--season",
            default=None,
            help="build only fixtures in this season, e.g. Spring",
        )
        parser.add_argument(
            "--year", type=int, default=None, help="build only fixtures in this year"
        )
        parser.add_argument(
            "--out", default=None, help="directory to write to; defaults to prompts/"
        )

    def handle(self, *args, **options):
        try:
            fixtures = select_fixtures(options["eval_set"], options["fixture"])
        except FixtureError as e:
            raise CommandError(str(e)) from e
        fixtures = [
            fixture
            for fixture in fixtures
            if options["season"] in (None, fixture["phase"]["season"])
            and options["year"] in (None, fixture["phase"]["year"])
        ]
        if not fixtures:
            raise CommandError("no fixture matches")
        out = Path(options["out"]) if options["out"] else PROMPTS_DIR
        variants = options["variant"] or list(VARIANTS)
        files = {}
        for fixture in fixtures:
            context = fixture_to_context(fixture)
            for variant in variants:
                try:
                    text = f"{VARIANTS[variant](context)}\n"
                    fixture_to_sample(fixture, user=text)
                except PromptError as e:
                    raise CommandError(f"{fixture['id']} {variant}: {e}") from e
                files[out / fixture["id"] / f"{variant}.txt"] = text
        edited = [
            str(path)
            for path, text in files.items()
            if path.exists() and path.read_text() != text
        ]
        if edited:
            raise CommandError(f"refusing to overwrite {edited}")
        for path, text in files.items():
            if path.exists():
                self.stdout.write(f"unchanged {path}")
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            self.stdout.write(f"wrote {path}")
