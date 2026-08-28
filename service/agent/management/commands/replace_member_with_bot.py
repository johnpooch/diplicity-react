from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agent.constants import AgentTaskKind
from agent.models import AgentTask
from game.models import Game
from member.models import Member
from phase.models import Phase
from user_profile.models import UserProfile


class Command(BaseCommand):
    help = "Replace a game member with a bot, seating the bot in that member's nation."

    def add_arguments(self, parser):
        parser.add_argument("--game", required=True, help="game id")
        parser.add_argument("--nation", required=True, help="nation of the member to replace")
        parser.add_argument("--bot", required=True, help="username of the bot to seat")

    def handle(self, *args, **options):
        game = Game.objects.filter(id=options["game"]).first()
        if game is None:
            raise CommandError(f"no game with id '{options['game']}'")

        member = (
            game.members.filter(nation__name__iexact=options["nation"], replaced_by__isnull=True)
            .select_related("nation", "user")
            .first()
        )
        if member is None:
            raise CommandError(f"game '{game.id}' has no member for nation '{options['nation']}'")
        if member.is_bot:
            raise CommandError(f"{member.nation.name} in game '{game.id}' is already played by a bot")

        available = UserProfile.objects.addable_to_game(game)
        bot_profile = available.filter(user__username=options["bot"]).first()
        if bot_profile is None:
            usernames = ", ".join(profile.user.username for profile in available)
            raise CommandError(f"no bot '{options['bot']}' available for game '{game.id}'; available: {usernames}")

        with transaction.atomic():
            replacement = Member.objects.hand_over_seat(member, bot_profile.user)

            phase = game.current_phase
            if phase is not None and Phase.objects.lock_if_active(phase.id) is not None:
                AgentTask.objects.enqueue(kind=AgentTaskKind.PLAN, member=replacement, phase=phase)

        self.stdout.write(
            self.style.SUCCESS(f"{bot_profile.name} now plays {member.nation.name} in '{game.id}'.")
        )
