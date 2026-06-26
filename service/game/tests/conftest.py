import pytest

from common.constants import GameStatus
from game.models import Game


@pytest.fixture
def player_run_active_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Player Run Game",
            status=GameStatus.ACTIVE,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[2])
        return game, primary_member, secondary_member, tertiary_member

    return _create


@pytest.fixture
def player_run_pending_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Player Run Pending Game",
            status=GameStatus.PENDING,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[2])
        return game, primary_member, secondary_member, tertiary_member

    return _create


@pytest.fixture
def game_master_game_factory(db, classical_variant, primary_user, secondary_user, tertiary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="GM Game",
            status=GameStatus.ACTIVE,
            created_by=primary_user,
            game_master=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        secondary_member = game.members.create(user=secondary_user, nation=nations[0])
        tertiary_member = game.members.create(user=tertiary_user, nation=nations[1])
        return game, secondary_member, tertiary_member

    return _create


@pytest.fixture
def management_transfer_sandbox_game_factory(db, classical_variant, primary_user, secondary_user):
    def _create():
        game = Game.objects.create(
            variant=classical_variant,
            name="Sandbox Game",
            status=GameStatus.ACTIVE,
            sandbox=True,
            created_by=primary_user,
        )
        nations = list(classical_variant.nations.filter(non_playable=False))
        primary_member = game.members.create(user=primary_user, nation=nations[0])
        secondary_member = game.members.create(user=secondary_user, nation=nations[1])
        return game, primary_member, secondary_member

    return _create
