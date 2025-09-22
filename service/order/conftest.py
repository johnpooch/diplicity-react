import pytest
from .models import Order
from django.apps import apps


Game = apps.get_model("game", "Game")
Phase = apps.get_model("game", "Phase")


@pytest.fixture
def base_active_game_for_primary_user(db, classical_variant):
    return Game.objects.create(
        name="Primary User's Active Game",
        variant=classical_variant,
        status=Game.ACTIVE,
    )


@pytest.fixture
def base_active_phase(db):
    def _create_phase(game):
        phase = game.phases.create(
            season="Spring",
            year=1901,
            type="Movement",
            status=Phase.ACTIVE,
        )
        phase.units.create(type="Fleet", nation="England", province="edi")
        phase.supply_centers.create(nation="England", province="edi")
        return phase

    return _create_phase


@pytest.fixture
def active_game(db, primary_user, secondary_user, base_active_game_for_primary_user, base_active_phase):
    phase = base_active_phase(base_active_game_for_primary_user)
    primary_member = base_active_game_for_primary_user.members.create(user=primary_user, nation="England")
    secondary_member = base_active_game_for_primary_user.members.create(user=secondary_user, nation="France")
    phase.phase_states.create(member=primary_member)
    phase.phase_states.create(member=secondary_member)
    return base_active_game_for_primary_user


@pytest.fixture
def test_phase_state(active_game, primary_user):
    return active_game.current_phase.phase_states.get(member__user=primary_user)
