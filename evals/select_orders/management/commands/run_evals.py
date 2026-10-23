import os
import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from inspect_ai import eval as inspect_eval

from select_orders.evals import select_orders
from select_orders.exceptions import FixtureError, PromptError
from select_orders.prompt_names import prompt_digest, prompt_name

NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


class Command(BaseCommand):
    help = "Run the select_orders evals against the real model"

    def add_arguments(self, parser):
        parser.add_argument("--model", default=settings.EVALS_MODEL)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--eval-set", default=settings.EVALS_EVAL_SET)
        parser.add_argument("--fixture", default=None, help="run only this fixture of the eval set")
        parser.add_argument("--system-file", default=None, help="send this text as the system prompt")
        parser.add_argument("--user-file", default=None, help="send this text as the user prompt")
        parser.add_argument(
            "--user-variant",
            default=None,
            help="send each fixture its prompts/<fixture>/<variant>.txt as the user prompt",
        )
        parser.add_argument("--prompt-name", default=None, help="name the prompt this instead of naming it by its hash")
        parser.add_argument("--epochs", type=int, default=1, help="model calls per fixture; each one is billed")

    def handle(self, *args, **options):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.stdout.write("skip: ANTHROPIC_API_KEY is not set")
            return
        if options["prompt_name"] is not None and not NAME.fullmatch(options["prompt_name"]):
            raise CommandError("a prompt name is lowercase letters, digits and single hyphens")
        system_file, user_file = (self._prompt_file(options[key]) for key in ("system_file", "user_file"))
        try:
            task = select_orders(
                options["eval_set"], options["fixture"], system_file, user_file, options["user_variant"]
            )
        except (FixtureError, PromptError) as e:
            raise CommandError(str(e)) from e
        digest = prompt_digest(task.dataset)
        name = options["prompt_name"] or prompt_name(digest, settings.EVALS_LOGS_DIR, date.today())
        self.stdout.write(f"prompt: {name}")
        inspect_eval(
            task,
            model=options["model"],
            limit=options["limit"],
            epochs=options["epochs"],
            log_dir=str(settings.EVALS_LOGS_DIR),
            metadata={"prompt": {"name": name, "digest": digest}},
        )

    def _prompt_file(self, path: str | None) -> str | None:
        if path is None:
            return None
        if not Path(path).is_file():
            raise CommandError(f"prompt file '{path}' does not exist")
        return str(Path(path).resolve())
