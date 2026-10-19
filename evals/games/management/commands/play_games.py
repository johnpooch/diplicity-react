import os
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from inspect_ai import eval as inspect_eval

from games.evals import opening_prompts, play_game
from games.play import nations
from select_orders.prompt_names import game_prompt_digest, prompt_name


class Command(BaseCommand):
    help = "Play games with the model in one seat and dumbbot in the other six"

    def add_arguments(self, parser):
        parser.add_argument("--nation", required=True)
        parser.add_argument("--games", type=int, default=1, help="games to play; each one is billed")
        parser.add_argument("--first-seed", type=int, default=0)
        parser.add_argument("--model", default=settings.EVALS_MODEL)

    def handle(self, *args, **options):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            self.stdout.write("skip: ANTHROPIC_API_KEY is not set")
            return
        nation = options["nation"]
        if nation not in nations():
            raise CommandError(f"unknown nation '{nation}'; choose from {nations()}")
        digest = game_prompt_digest(nation, *opening_prompts(nation))
        name = prompt_name(digest, settings.EVALS_LOGS_DIR, date.today())
        self.stdout.write(f"prompt: {name}")
        inspect_eval(
            play_game(nation, options["first_seed"], options["games"]),
            model=options["model"],
            log_dir=str(settings.EVALS_LOGS_DIR),
            metadata={"prompt": {"name": name, "digest": digest}},
        )
