import pytest
from game import models
from common.constants import PhaseStatus, GameStatus


@pytest.fixture
def base_pending_phase(db, classical_england_nation, classical_edinburgh_province):
    def _create_phase(game):
        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.PENDING,
            ordinal=0,
        )
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)
        return phase

    return _create_phase


@pytest.fixture
def base_pending_game_for_secondary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Secondary User's Pending Game",
        variant=classical_variant,
        status=GameStatus.PENDING,
    )
