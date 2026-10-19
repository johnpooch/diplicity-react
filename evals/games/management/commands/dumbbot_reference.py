from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from games.play import nations
from games.reference import reference_game, write_reference


class Command(BaseCommand):
    help = "Play all-dumbbot games on seeds 0..N-1 and write the reference band for one nation"

    def add_arguments(self, parser):
        parser.add_argument("--nation", required=True)
        parser.add_argument("--seeds", type=int, default=100)

    def handle(self, *args, **options):
        nation = options["nation"]
        if nation not in nations():
            raise CommandError(f"unknown nation '{nation}'; choose from {nations()}")
        games = [reference_game(seed, nation) for seed in range(options["seeds"])]
        path = write_reference(settings.EVALS_REFERENCE_DIR, nation, games)
        self.stdout.write(f"wrote {path}")
