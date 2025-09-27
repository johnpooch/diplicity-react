import pytest
from .models import Order
from django.apps import apps
from common.constants import PhaseStatus
from nation.models import Nation
from province.models import Province


Game = apps.get_model("game", "Game")
Phase = apps.get_model("phase", "Phase")


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
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        # Get the actual model instances
        england_nation = Nation.objects.get(name="England", variant=game.variant)
        edi_province = Province.objects.get(province_id="edi", variant=game.variant)

        phase.units.create(type="Fleet", nation=england_nation, province=edi_province)
        phase.supply_centers.create(nation=england_nation, province=edi_province)
        return phase

    return _create_phase


@pytest.fixture
def order_active_game(db, primary_user, secondary_user, base_active_game_for_primary_user, base_active_phase):
    phase = base_active_phase(base_active_game_for_primary_user)

    # Get the actual nation instances
    england_nation = Nation.objects.get(name="England", variant=base_active_game_for_primary_user.variant)
    france_nation = Nation.objects.get(name="France", variant=base_active_game_for_primary_user.variant)

    primary_member = base_active_game_for_primary_user.members.create(user=primary_user, nation=england_nation)
    secondary_member = base_active_game_for_primary_user.members.create(user=secondary_user, nation=france_nation)
    phase.phase_states.create(member=primary_member)
    phase.phase_states.create(member=secondary_member)
    return base_active_game_for_primary_user


@pytest.fixture
def test_phase_state(order_active_game, primary_user):
    return order_active_game.current_phase.phase_states.get(member__user=primary_user)
