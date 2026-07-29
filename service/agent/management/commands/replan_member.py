from django.core.management.base import BaseCommand, CommandError

from agent.replan import ReplanError, replan
from game.models import Game


class Command(BaseCommand):
    help = "Re-plan a bot member's orders for the current phase."

    def add_arguments(self, parser):
        parser.add_argument("--game", required=True, help="game id")
        parser.add_argument("--nation", required=True, help="nation of the bot member to re-plan")

    def handle(self, *args, **options):
        game = Game.objects.filter(id=options["game"]).first()
        if game is None:
            raise CommandError(f"no game with id '{options['game']}'")

        member = (
            game.members.not_replaced()
            .filter(nation__name__iexact=options["nation"])
            .select_related("nation", "user", "game")
            .first()
        )
        if member is None:
            raise CommandError(f"game '{game.id}' has no member for nation '{options['nation']}'")

        try:
            replan(member)
        except ReplanError as e:
            raise CommandError(str(e))

        self.stdout.write(self.style.SUCCESS(f"Queued a re-plan for {member.nation.name} in '{game.id}'."))
