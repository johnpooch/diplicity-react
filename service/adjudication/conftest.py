import pytest
from game.models import Game
from common.constants import GameStatus
from member.models import Member
from phase.models import Phase


@pytest.fixture
def game(italy_vs_germany_variant):
    return Game.objects.create(variant=italy_vs_germany_variant, name="Test Game", status=GameStatus.ACTIVE)


@pytest.fixture
def member_italy(italy_vs_germany_variant, italy_vs_germany_italy_nation, primary_user, game):
    return Member.objects.create(nation=italy_vs_germany_italy_nation, user=primary_user, game=game)


@pytest.fixture
def member_germany(italy_vs_germany_variant, italy_vs_germany_germany_nation, secondary_user, game):
    return Member.objects.create(nation=italy_vs_germany_germany_nation, user=secondary_user, game=game)


@pytest.fixture
def phase_spring_1901_movement(game):
    return Phase.objects.create(game=game, variant=game.variant, season="Spring", year=1901, type="Movement", ordinal=1)


@pytest.fixture
def phase_spring_1901_retreat(game):
    return Phase.objects.create(game=game, variant=game.variant, season="Spring", year=1901, type="Retreat", ordinal=2)


@pytest.fixture
def phase_fall_1901_movement(game):
    return Phase.objects.create(game=game, variant=game.variant, season="Fall", year=1901, type="Movement", ordinal=3)


@pytest.fixture
def phase_fall_1901_retreat(game):
    return Phase.objects.create(game=game, variant=game.variant, season="Fall", year=1901, type="Retreat", ordinal=4)


@pytest.fixture
def phase_fall_1901_adjustment(game):
    return Phase.objects.create(game=game, variant=game.variant, season="Fall", year=1901, type="Adjustment", ordinal=5)
