import pytest
from django.contrib.auth import get_user_model

from common.constants import GameStatus, PhaseStatus
from game.models import Game
from notification.models import Notification
from phase.models import Phase
from user_profile.models import UserProfile

User = get_user_model()


@pytest.fixture
def committed_draw_game(
    django_db_blocker,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
):
    with django_db_blocker.unblock():
        users = []
        for name in ("committeditaly", "committedgermany"):
            user = User.objects.create_user(
                username=name, email=f"{name}@example.com", password="testpass123"
            )
            UserProfile.objects.create(user=user, name=name, picture="")
            users.append(user)
        game = Game.objects.create(
            name="Committed Draw Game",
            variant=italy_vs_germany_variant,
            status=GameStatus.ACTIVE,
        )
        phase = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        nations = (italy_vs_germany_italy_nation, italy_vs_germany_germany_nation)
        for user, nation in zip(users, nations):
            member = game.members.create(user=user, nation=nation)
            phase.phase_states.create(member=member, has_possible_orders=True)

    yield game, phase, users

    with django_db_blocker.unblock():
        Notification.objects.filter(recipient__in=users).delete()
        game.delete()
        for user in users:
            user.delete()
