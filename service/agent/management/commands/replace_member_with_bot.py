from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agent.constants import AgentTaskKind
from agent.models import AgentTask
from bot_profile.models import BotProfile
from common.constants import PhaseStatus
from game.models import Game


class Command(BaseCommand):
    help = "Seat a bot in a game member's nation, replacing whoever holds it."

    def add_arguments(self, parser):
        parser.add_argument("--game", required=True, help="game id")
        parser.add_argument("--nation", required=True, help="nation of the member to replace")
        parser.add_argument("--bot", required=True, help="username of the bot to seat")

    def handle(self, *args, **options):
        game = Game.objects.filter(id=options["game"]).first()
        if game is None:
            raise CommandError(f"no game with id '{options['game']}'")

        member = game.members.filter(nation__name__iexact=options["nation"]).select_related("nation").first()
        if member is None:
            raise CommandError(f"game '{game.id}' has no member for nation '{options['nation']}'")

        available = BotProfile.objects.available_for_game(game)
        bot_profile = available.filter(user__username=options["bot"]).first()
        if bot_profile is None:
            usernames = ", ".join(profile.user.username for profile in available)
            raise CommandError(f"no bot '{options['bot']}' available for game '{game.id}'; available: {usernames}")

        with transaction.atomic():
            member.user = bot_profile.user
            member.kicked = False
            member.civil_disorder = False
            member.save(update_fields=["user", "kicked", "civil_disorder"])

            phase = game.current_phase
            if phase is not None and phase.status == PhaseStatus.ACTIVE:
                AgentTask.objects.create_from_event(kind=AgentTaskKind.PLAN, member=member, phase=phase)

        self.stdout.write(
            self.style.SUCCESS(f"{bot_profile.user.profile.name} now plays {member.nation.name} in '{game.id}'.")
        )
