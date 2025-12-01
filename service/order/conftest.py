import pytest
from django.apps import apps
from common.constants import PhaseStatus, GameStatus
from nation.models import Nation
from province.models import Province


Game = apps.get_model("game", "Game")
Phase = apps.get_model("phase", "Phase")


@pytest.fixture
def base_active_game_for_primary_user(db, classical_variant):
    return Game.objects.create(
        name="Primary User's Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
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


@pytest.fixture
def game_with_many_phase_states(primary_user, classical_variant):
    from common.constants import PhaseStatus, GameStatus, UnitType
    from user_profile.models import User

    game = Game.objects.create(
        name="Game with Many Phase States",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )

    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )

    all_nations = Nation.objects.filter(variant=classical_variant).order_by("id")

    for i, nation in enumerate(all_nations):
        if i == 0:
            user = primary_user
        else:
            user = User.objects.create_user(
                username=f"user_{nation.name.lower()}",
                email=f"{nation.name.lower()}@test.com",
                password="testpass123"
            )

        member = game.members.create(user=user, nation=nation)
        phase.phase_states.create(member=member)

        province_ids = {
            "England": "lon",
            "France": "par",
            "Germany": "ber",
            "Italy": "rom",
            "Austria": "vie",
            "Turkey": "con",
            "Russia": "mos"
        }

        province_id = province_ids.get(nation.name)
        if province_id:
            province = Province.objects.get(province_id=province_id, variant=classical_variant)
            phase.units.create(type=UnitType.ARMY, nation=nation, province=province)

    phase.options = {
        "England": {
            "bud": {
                "Next": {
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"},
                                },
                                "Type": "SrcProvince",
                            }
                        },
                        "Type": "OrderType",
                    },
                },
                "Type": "Province",
            },
        },
    }
    phase.save()

    return game
