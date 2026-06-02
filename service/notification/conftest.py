import pytest
from game.models import Game
from phase.models import Phase
from common.constants import GameStatus, PhaseStatus


@pytest.fixture
def make_draw_notification_game(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create():
        game = Game.objects.create(
            name="Draw Notification Test",
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
        italy = game.members.create(user=primary_user, nation=italy_vs_germany_italy_nation)
        germany = game.members.create(user=secondary_user, nation=italy_vs_germany_germany_nation)
        phase.phase_states.create(member=italy, has_possible_orders=True)
        phase.phase_states.create(member=germany, has_possible_orders=True)
        return game, italy, germany

    return _create


@pytest.fixture
def make_end_game_notification_game(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create():
        game = Game.objects.create(
            name="End Game Test",
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
        italy = game.members.create(user=primary_user, nation=italy_vs_germany_italy_nation)
        germany = game.members.create(user=secondary_user, nation=italy_vs_germany_germany_nation)
        return game, phase, italy, germany

    return _create
