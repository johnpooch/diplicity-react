import pytest
from datetime import timedelta
from django.utils import timezone
from phase.models import Phase
from common.constants import PhaseStatus, UnitType, OrderType, GameStatus, MovementPhaseDuration


@pytest.fixture
def italy_vs_germany_phase_with_orders(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    italy_vs_germany_venice_province,
    italy_vs_germany_rome_province,
    italy_vs_germany_naples_province,
    italy_vs_germany_kiel_province,
    italy_vs_germany_berlin_province,
    italy_vs_germany_munich_province,
    primary_user,
    secondary_user,
):
    from game.models import Game
    from member.models import Member

    game = Game.objects.create(
        variant=italy_vs_germany_variant,
        name="Test Game",
        status=GameStatus.ACTIVE,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )

    member_italy = Member.objects.create(
        nation=italy_vs_germany_italy_nation,
        user=primary_user,
        game=game,
    )

    member_germany = Member.objects.create(
        nation=italy_vs_germany_germany_nation,
        user=secondary_user,
        game=game,
    )

    phase = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status=PhaseStatus.ACTIVE,
    )

    phase_state_italy = phase.phase_states.create(member=member_italy)
    phase_state_germany = phase.phase_states.create(member=member_germany)

    phase.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)

    phase.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    phase.units.create(province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase.units.create(province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase.units.create(province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation)

    phase.units.create(province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation)
    phase.units.create(province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)
    phase.units.create(province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)

    phase_state_italy.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )

    phase_state_germany.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )

    return phase


@pytest.fixture
def mock_adjudication_data_basic():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
        "options": {},
        "supply_centers": [
            {"province": "ven", "nation": "Italy"},
            {"province": "rom", "nation": "Italy"},
            {"province": "nap", "nation": "Italy"},
            {"province": "kie", "nation": "Germany"},
            {"province": "ber", "nation": "Germany"},
            {"province": "mun", "nation": "Germany"},
        ],
        "units": [
            {"type": "Army", "nation": "Italy", "province": "ven", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Italy", "province": "rom", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "mun", "dislodged": False, "dislodged_by": None},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
        ],
    }


@pytest.fixture
def mock_adjudication_data_with_dislodged_unit():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
        "options": {},
        "supply_centers": [
            {"province": "ven", "nation": "Italy"},
            {"province": "rom", "nation": "Italy"},
            {"province": "nap", "nation": "Italy"},
            {"province": "kie", "nation": "Germany"},
        ],
        "units": [
            {"type": "Army", "nation": "Italy", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Italy", "province": "rom", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "kie", "dislodged": True, "dislodged_by": "ven"},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
        ],
    }


@pytest.fixture
def game_with_three_phases(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    italy_vs_germany_venice_province,
    italy_vs_germany_rome_province,
    italy_vs_germany_naples_province,
    italy_vs_germany_kiel_province,
    italy_vs_germany_berlin_province,
    italy_vs_germany_munich_province,
    primary_user,
    secondary_user,
):
    from game.models import Game
    from member.models import Member
    from order.models import OrderResolution

    game = Game.objects.create(
        variant=italy_vs_germany_variant,
        name="Test Game with Multiple Phases",
        status=GameStatus.ACTIVE,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )

    member_italy = Member.objects.create(
        nation=italy_vs_germany_italy_nation,
        user=primary_user,
        game=game,
    )

    member_germany = Member.objects.create(
        nation=italy_vs_germany_germany_nation,
        user=secondary_user,
        game=game,
    )

    phase1 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status=PhaseStatus.COMPLETED,
    )

    phase_state_italy_1 = phase1.phase_states.create(member=member_italy)
    phase_state_germany_1 = phase1.phase_states.create(member=member_germany)

    phase1.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase1.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase1.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    unit1 = phase1.units.create(province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase1.units.create(province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase1.units.create(province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation)
    phase1.units.create(province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation)
    phase1.units.create(province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)
    phase1.units.create(province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)

    order1 = phase_state_italy_1.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order1, status="OK")

    order2 = phase_state_germany_1.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order2, status="OK")

    phase2 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Fall",
        year=1901,
        type="Movement",
        ordinal=2,
        status=PhaseStatus.COMPLETED,
    )

    phase_state_italy_2 = phase2.phase_states.create(member=member_italy)
    phase_state_germany_2 = phase2.phase_states.create(member=member_germany)

    phase2.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase2.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase2.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    phase2.units.create(province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase2.units.create(province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase2.units.create(province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation)
    phase2.units.create(province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation)
    phase2.units.create(province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)
    phase2.units.create(province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)

    order3 = phase_state_italy_2.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order3, status="OK")

    phase3 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1902,
        type="Movement",
        ordinal=3,
        status=PhaseStatus.ACTIVE,
    )

    phase_state_italy_3 = phase3.phase_states.create(member=member_italy, orders_confirmed=True)
    phase_state_germany_3 = phase3.phase_states.create(member=member_germany, orders_confirmed=False)

    phase3.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase3.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)

    phase3.units.create(province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase3.units.create(province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation)
    phase3.units.create(province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation)
    phase3.units.create(province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation)
    phase3.units.create(province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation)

    phase_state_italy_3.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )

    phase_state_germany_3.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )

    return game


@pytest.fixture
def phase_factory(db, classical_variant, primary_user, secondary_user):
    from game.models import Game
    from member.models import Member

    def _create_phase(
        scheduled_resolution=None,
        phase_states_config=None,
        status=PhaseStatus.ACTIVE,
        game=None,
        options=None,
    ):
        if game is None:
            game = Game.objects.create(
                variant=classical_variant,
                name=f"Test Game {Phase.objects.count()}",
                status=GameStatus.ACTIVE,
                movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            )

        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=status,
            scheduled_resolution=scheduled_resolution,
            options=options or {},
        )

        if phase_states_config:
            for config in phase_states_config:
                nation = config.get('nation')
                if not nation:
                    continue

                member = game.members.filter(nation=nation).first()
                if not member:
                    user = config.get('user', primary_user)
                    member = Member.objects.create(
                        nation=nation,
                        user=user,
                        game=game,
                    )

                phase.phase_states.create(
                    member=member,
                    has_possible_orders=config.get('has_possible_orders', False),
                    orders_confirmed=config.get('orders_confirmed', False),
                )

        return phase

    return _create_phase


@pytest.fixture
def multiple_games_with_phases(
    db,
    classical_variant,
    primary_user,
    secondary_user,
    classical_england_nation,
    classical_france_nation,
):
    from game.models import Game
    from member.models import Member

    games_data = []

    for i in range(3):
        game = Game.objects.create(
            variant=classical_variant,
            name=f"Multi Game {i}",
            status=GameStatus.ACTIVE,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )

        member_england = Member.objects.create(
            nation=classical_england_nation,
            user=primary_user,
            game=game,
        )

        member_france = Member.objects.create(
            nation=classical_france_nation,
            user=secondary_user,
            game=game,
        )

        if i == 0:
            scheduled_resolution = timezone.now() - timedelta(hours=1)
            has_possible_orders_england = True
            has_possible_orders_france = True
            orders_confirmed_england = False
            orders_confirmed_france = False
        elif i == 1:
            scheduled_resolution = timezone.now() + timedelta(hours=24)
            has_possible_orders_england = True
            has_possible_orders_france = True
            orders_confirmed_england = True
            orders_confirmed_france = True
        else:
            scheduled_resolution = timezone.now() + timedelta(hours=24)
            has_possible_orders_england = True
            has_possible_orders_france = True
            orders_confirmed_england = True
            orders_confirmed_france = False

        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=scheduled_resolution,
        )

        phase.phase_states.create(
            member=member_england,
            has_possible_orders=has_possible_orders_england,
            orders_confirmed=orders_confirmed_england,
        )

        phase.phase_states.create(
            member=member_france,
            has_possible_orders=has_possible_orders_france,
            orders_confirmed=orders_confirmed_france,
        )

        games_data.append({
            'game': game,
            'phase': phase,
            'should_resolve': i in [0, 1],
        })

    return games_data
