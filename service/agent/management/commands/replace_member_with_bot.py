from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from agent.constants import AgentTaskKind
from agent.models import AgentTask
from bot_profile.models import BotProfile
from channel.models import ChannelMember
from game.models import Game
from order.models import Order
from phase.models import Phase, PhaseState


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
        if member.user is not None and hasattr(member.user, "bot_profile"):
            raise CommandError(f"{member.nation.name} in game '{game.id}' is already played by a bot")

        available = BotProfile.objects.available_for_game(game)
        bot_profile = available.filter(user__username=options["bot"]).first()
        if bot_profile is None:
            usernames = ", ".join(profile.user.username for profile in available)
            raise CommandError(f"no bot '{options['bot']}' available for game '{game.id}'; available: {usernames}")

        with transaction.atomic():
            replacement = game.members.create(user=bot_profile.user, nation=member.nation)
            ChannelMember.objects.bulk_create(
                [
                    ChannelMember(member=replacement, channel_id=channel_id)
                    for channel_id in member.member_channels.values_list("channel_id", flat=True)
                ]
            )

            member.kicked = True
            member.replaced_by = replacement
            member.save(update_fields=["kicked", "replaced_by"])

            phase = game.current_phase
            if phase is not None and Phase.objects.lock_if_active(phase.id) is not None:
                replaced_states = phase.phase_states.filter(member=member)
                Order.objects.filter(phase_state__in=replaced_states).delete()
                replaced_states.update(has_possible_orders=False)
                PhaseState.objects.create(
                    member=replacement,
                    phase=phase,
                    has_possible_orders=member.nation.name in phase.nations_with_possible_orders,
                )
                AgentTask.objects.enqueue(kind=AgentTaskKind.PLAN, member=replacement, phase=phase)

        self.stdout.write(
            self.style.SUCCESS(f"{bot_profile.user.profile.name} now plays {member.nation.name} in '{game.id}'.")
        )
