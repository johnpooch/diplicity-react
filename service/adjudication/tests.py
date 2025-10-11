import pytest
from phase.models import Phase
from game.models import Game
from member.models import Member
import adjudication.service as adjudication_service
from adjudication.serializers import AdjudicationSerializer
from common.constants import GameStatus, OrderType, UnitType


def sort_by_province(supply_centers):
    return sorted(supply_centers, key=lambda x: x["province"])


def create_order(phase_state, source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
    source = phase_state.phase.variant.provinces.get(province_id=source)
    target = phase_state.phase.variant.provinces.get(province_id=target) if target else None
    aux = phase_state.phase.variant.provinces.get(province_id=aux) if aux else None
    named_coast = phase_state.phase.variant.provinces.get(province_id=named_coast) if named_coast else None
    phase_state.orders.create(
        source=source,
        order_type=order_type,
        target=target,
        aux=aux,
        unit_type=unit_type,
        named_coast=named_coast,
    )


def create_unit(phase_state, province, unit_type):
    province = phase_state.phase.variant.provinces.get(province_id=province)
    phase_state.phase.units.create(province=province, type=unit_type, nation=phase_state.member.nation)


def create_supply_center(phase_state, province):
    province = phase_state.phase.variant.provinces.get(province_id=province)
    phase_state.phase.supply_centers.create(province=province, nation=phase_state.member.nation)


def setup_classical_opening(phase, members_by_nation):
    classical_opening = {
        "England": {
            "units": [
                {"province": "edi", "type": "Fleet"},
                {"province": "lvp", "type": "Army"},
                {"province": "lon", "type": "Fleet"},
            ],
            "supply_centers": ["edi", "lvp", "lon"],
        },
        "France": {
            "units": [
                {"province": "bre", "type": "Fleet"},
                {"province": "par", "type": "Army"},
                {"province": "mar", "type": "Army"},
            ],
            "supply_centers": ["bre", "par", "mar"],
        },
        "Germany": {
            "units": [
                {"province": "kie", "type": "Fleet"},
                {"province": "ber", "type": "Army"},
                {"province": "mun", "type": "Army"},
            ],
            "supply_centers": ["kie", "ber", "mun"],
        },
        "Italy": {
            "units": [
                {"province": "ven", "type": "Army"},
                {"province": "rom", "type": "Army"},
                {"province": "nap", "type": "Fleet"},
            ],
            "supply_centers": ["ven", "rom", "nap"],
        },
        "Austria": {
            "units": [
                {"province": "tri", "type": "Fleet"},
                {"province": "vie", "type": "Army"},
                {"province": "bud", "type": "Army"},
            ],
            "supply_centers": ["tri", "vie", "bud"],
        },
        "Russia": {
            "units": [
                {"province": "stp/sc", "type": "Fleet"},
                {"province": "mos", "type": "Army"},
                {"province": "war", "type": "Army"},
                {"province": "sev", "type": "Fleet"},
            ],
            "supply_centers": ["stp", "mos", "war", "sev"],
        },
        "Turkey": {
            "units": [
                {"province": "con", "type": "Army"},
                {"province": "smy", "type": "Army"},
                {"province": "ank", "type": "Fleet"},
            ],
            "supply_centers": ["con", "smy", "ank"],
        },
    }

    for nation_name, data in classical_opening.items():
        if nation_name not in members_by_nation:
            continue

        member = members_by_nation[nation_name]
        phase_state = phase.phase_states.create(member=member)

        for sc_id in data["supply_centers"]:
            create_supply_center(phase_state, sc_id)

        for unit_data in data["units"]:
            create_unit(phase_state, unit_data["province"], unit_data["type"])


class TestAdjudicationService:
    @pytest.mark.django_db
    def test_start_classical(self, classical_variant, classical_england_nation, classical_edinburgh_province):
        game = Game.objects.create(variant=classical_variant, name="Test Game", status=GameStatus.ACTIVE)
        phase = Phase.objects.create(
            variant=classical_variant, game=game, year=1901, season="Spring", type="Movement", ordinal=1
        )
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

        data = adjudication_service.start(phase)

        assert isinstance(data["options"], dict)
        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Movement"
        assert data["supply_centers"][0] == {"nation": "Turkey", "province": "ank"}
        assert data["units"][0] == {"dislodged_by": None, "type": "Fleet", "nation": "Turkey", "province": "ank"}
        assert data["resolutions"] == []

    @pytest.mark.django_db
    def test_resolve_italy_vs_germany_spring_1901_movement(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Standard opening phase of Italy vs Germany.

        Army Venice moves to Trieste.
        Army Rome moves to Naples.
        Fleet Naples moves to Ionian Sea.

        Fleet Kiel moves to Denmark.
        Army Berlin moves to Prussia.
        Army Munich moves to Ruhr.

        All orders are resolved successfully.
        """
        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_spring_1901_movement.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "rom")
        create_supply_center(phase_state_italy, "nap")

        create_supply_center(phase_state_germany, "kie")
        create_supply_center(phase_state_germany, "ber")
        create_supply_center(phase_state_germany, "mun")

        create_unit(phase_state_italy, "ven", "Army")
        create_unit(phase_state_italy, "rom", "Army")
        create_unit(phase_state_italy, "nap", "Fleet")

        create_unit(phase_state_germany, "kie", "Fleet")
        create_unit(phase_state_germany, "ber", "Army")
        create_unit(phase_state_germany, "mun", "Army")

        create_order(phase_state_italy, "ven", OrderType.MOVE, "tri")
        create_order(phase_state_italy, "rom", OrderType.MOVE, "nap")
        create_order(phase_state_italy, "nap", OrderType.MOVE, "ion")

        create_order(phase_state_germany, "kie", OrderType.MOVE, "den")
        create_order(phase_state_germany, "ber", OrderType.MOVE, "pru")
        create_order(phase_state_germany, "mun", OrderType.MOVE, "ruh")

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"
        assert len(data["options"]) == 2

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "nap", "nation": "Italy"},
                {"province": "rom", "nation": "Italy"},
                {"province": "ven", "nation": "Italy"},
                {"province": "ber", "nation": "Germany"},
                {"province": "kie", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "nap", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "pru", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "ven", "result": "OK", "by": None},
                {"province": "rom", "result": "OK", "by": None},
                {"province": "nap", "result": "OK", "by": None},
                {"province": "kie", "result": "OK", "by": None},
                {"province": "ber", "result": "OK", "by": None},
                {"province": "mun", "result": "OK", "by": None},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_italy_vs_germany_spring_1901_retreat(
        self,
        phase_spring_1901_retreat,
        member_italy,
        member_germany,
    ):
        """
        Retreat phase following the Spring 1901 movement.

        Units are in resolved positions with no orders.
        """
        phase_state_italy = phase_spring_1901_retreat.phase_states.create(member=member_italy)
        phase_state_germany = phase_spring_1901_retreat.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "rom")
        create_supply_center(phase_state_italy, "nap")

        create_supply_center(phase_state_germany, "kie")
        create_supply_center(phase_state_germany, "ber")
        create_supply_center(phase_state_germany, "mun")

        create_unit(phase_state_italy, "tri", "Army")
        create_unit(phase_state_italy, "nap", "Army")
        create_unit(phase_state_italy, "ion", "Fleet")

        create_unit(phase_state_germany, "den", "Fleet")
        create_unit(phase_state_germany, "pru", "Army")
        create_unit(phase_state_germany, "ruh", "Army")

        data = adjudication_service.resolve(phase_spring_1901_retreat)

        assert data["year"] == 1901
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "ven", "nation": "Italy"},
                {"province": "rom", "nation": "Italy"},
                {"province": "nap", "nation": "Italy"},
                {"province": "kie", "nation": "Germany"},
                {"province": "ber", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "nap", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "pru", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged_by": None},
            ]
        )

        assert data["resolutions"] == []

    @pytest.mark.django_db
    def test_resolve_italy_vs_germany_fall_1901_movement(
        self,
        phase_fall_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Fall 1901 movement phase with convoy and movement orders.

        Fleet Ionian Sea convoys Army Naples to Greece.
        Army Naples moves to Greece (via convoy).
        Army Trieste holds.

        Army Prussia moves to Warsaw.
        Fleet Denmark holds.
        Army Ruhr holds.
        """
        phase_state_italy = phase_fall_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_fall_1901_movement.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "rom")
        create_supply_center(phase_state_italy, "nap")

        create_supply_center(phase_state_germany, "kie")
        create_supply_center(phase_state_germany, "ber")
        create_supply_center(phase_state_germany, "mun")

        create_unit(phase_state_italy, "tri", "Army")
        create_unit(phase_state_italy, "nap", "Army")
        create_unit(phase_state_italy, "ion", "Fleet")

        create_unit(phase_state_germany, "den", "Fleet")
        create_unit(phase_state_germany, "pru", "Army")
        create_unit(phase_state_germany, "ruh", "Army")

        create_order(phase_state_italy, "ion", OrderType.CONVOY, aux="nap", target="gre")
        create_order(phase_state_italy, "nap", OrderType.MOVE, "gre")
        create_order(phase_state_italy, "tri", OrderType.HOLD)

        create_order(phase_state_germany, "pru", OrderType.MOVE, "war")
        create_order(phase_state_germany, "den", OrderType.HOLD)
        create_order(phase_state_germany, "ruh", OrderType.HOLD)

        data = adjudication_service.resolve(phase_fall_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Fall"
        assert data["type"] == "Retreat"

        assert len(data["options"]) == 2
        assert data["options"]["Italy"] == {}
        assert data["options"]["Germany"] == {}

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "ven", "nation": "Italy"},
                {"province": "rom", "nation": "Italy"},
                {"province": "nap", "nation": "Italy"},
                {"province": "kie", "nation": "Germany"},
                {"province": "ber", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "ion", "result": "OK", "by": None},
                {"province": "nap", "result": "OK", "by": None},
                {"province": "tri", "result": "OK", "by": None},
                {"province": "pru", "result": "OK", "by": None},
                {"province": "den", "result": "OK", "by": None},
                {"province": "ruh", "result": "OK", "by": None},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_italy_vs_germany_fall_1901_retreat(
        self,
        phase_fall_1901_retreat,
        member_italy,
        member_germany,
    ):
        """
        Fall 1901 retreat phase with no orders following the movement phase.
        """
        phase_state_italy = phase_fall_1901_retreat.phase_states.create(member=member_italy)
        phase_state_germany = phase_fall_1901_retreat.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "rom")
        create_supply_center(phase_state_italy, "nap")

        create_supply_center(phase_state_germany, "kie")
        create_supply_center(phase_state_germany, "ber")
        create_supply_center(phase_state_germany, "mun")

        create_unit(phase_state_italy, "tri", "Army")
        create_unit(phase_state_italy, "gre", "Army")
        create_unit(phase_state_italy, "ion", "Fleet")

        create_unit(phase_state_germany, "den", "Fleet")
        create_unit(phase_state_germany, "war", "Army")
        create_unit(phase_state_germany, "ruh", "Army")

        data = adjudication_service.resolve(phase_fall_1901_retreat)

        assert data["year"] == 1901
        assert data["season"] == "Fall"
        assert data["type"] == "Adjustment"

        assert len(data["options"]) == 2

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "rom", "nation": "Italy"},
                {"province": "ven", "nation": "Italy"},
                {"province": "nap", "nation": "Italy"},
                {"province": "gre", "nation": "Italy"},
                {"province": "tri", "nation": "Italy"},
                {"province": "ber", "nation": "Germany"},
                {"province": "kie", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
                {"province": "den", "nation": "Germany"},
                {"province": "war", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged_by": None},
            ]
        )

        assert data["resolutions"] == []

    @pytest.mark.django_db
    def test_resolve_italy_vs_germany_fall_1901_adjustment(
        self,
        phase_fall_1901_adjustment,
        member_italy,
        member_germany,
    ):
        """
        Fall 1901 adjustment phase where both Italy and Germany build units.

        Italy builds an army and a fleet.
        Germany builds an army and a fleet.
        """
        phase_state_italy = phase_fall_1901_adjustment.phase_states.create(member=member_italy)
        phase_state_germany = phase_fall_1901_adjustment.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "rom")
        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "nap")
        create_supply_center(phase_state_italy, "gre")
        create_supply_center(phase_state_italy, "tri")

        create_supply_center(phase_state_germany, "ber")
        create_supply_center(phase_state_germany, "kie")
        create_supply_center(phase_state_germany, "mun")
        create_supply_center(phase_state_germany, "den")
        create_supply_center(phase_state_germany, "war")

        create_unit(phase_state_italy, "tri", "Army")
        create_unit(phase_state_italy, "gre", "Army")
        create_unit(phase_state_italy, "ion", "Fleet")

        create_unit(phase_state_germany, "den", "Fleet")
        create_unit(phase_state_germany, "war", "Army")
        create_unit(phase_state_germany, "ruh", "Army")

        create_order(phase_state_italy, "rom", OrderType.BUILD, unit_type="Army")
        create_order(phase_state_italy, "nap", OrderType.BUILD, unit_type="Fleet")

        create_order(phase_state_germany, "ber", OrderType.BUILD, unit_type="Army")
        create_order(phase_state_germany, "kie", OrderType.BUILD, unit_type="Fleet")

        data = adjudication_service.resolve(phase_fall_1901_adjustment)

        assert data["year"] == 1902
        assert data["season"] == "Spring"
        assert data["type"] == "Movement"

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "rom", "nation": "Italy"},
                {"province": "ven", "nation": "Italy"},
                {"province": "nap", "nation": "Italy"},
                {"province": "gre", "nation": "Italy"},
                {"province": "tri", "nation": "Italy"},
                {"province": "ber", "nation": "Germany"},
                {"province": "kie", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
                {"province": "den", "nation": "Germany"},
                {"province": "war", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "rom", "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ber", "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "rom", "result": "OK", "by": None},
                {"province": "nap", "result": "OK", "by": None},
                {"province": "ber", "result": "OK", "by": None},
                {"province": "kie", "result": "OK", "by": None},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_dislodgement_scenario(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Test unit dislodgement scenario.

        Italian Army Berlin moves to Kiel.
        Italian Army Munich supports Berlin to Kiel.
        German Army Kiel holds.

        The German army in Kiel should be dislodged by the Italian attack.
        """
        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_spring_1901_movement.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ber")
        create_supply_center(phase_state_italy, "mun")
        create_supply_center(phase_state_germany, "kie")

        create_unit(phase_state_italy, "ber", "Army")
        create_unit(phase_state_italy, "mun", "Army")
        create_unit(phase_state_germany, "kie", "Army")

        create_order(phase_state_italy, "ber", OrderType.MOVE, "kie")
        create_order(phase_state_italy, "mun", OrderType.SUPPORT, "kie", "ber")
        create_order(phase_state_germany, "kie", OrderType.HOLD)

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "ber", "nation": "Italy"},
                {"province": "mun", "nation": "Italy"},
                {"province": "kie", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "kie", "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "mun", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "kie", "dislodged_by": "ber"},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "ber", "result": "OK", "by": None},
                {"province": "mun", "result": "OK", "by": None},
                {"province": "kie", "result": "OK", "by": None},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_bounce_scenario(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Test unit bounce scenario where two units try to move to the same province.

        Italian Army Berlin moves to Munich.
        German Army Kiel moves to Munich.

        Both units should bounce and remain in their original positions.
        """
        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_spring_1901_movement.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ber")
        create_supply_center(phase_state_germany, "kie")

        create_unit(phase_state_italy, "ber", "Army")
        create_unit(phase_state_germany, "kie", "Army")

        create_order(phase_state_italy, "ber", OrderType.MOVE, "kie")
        create_order(phase_state_germany, "kie", OrderType.MOVE, "ber")

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "ber", "nation": "Italy"},
                {"province": "kie", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "ber", "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "kie", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "ber", "result": "ErrBounce", "by": "kie"},
                {"province": "kie", "result": "ErrBounce", "by": "ber"},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_bounce_scenario(
        self,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_italy_nation,
        classical_austria_nation,
        classical_russia_nation,
        classical_turkey_nation,
        primary_user,
        secondary_user,
        tertiary_user,
    ):
        game = Game.objects.create(variant=classical_variant, name="Classical Test Game", status=GameStatus.ACTIVE)

        members_by_nation = {
            "England": Member.objects.create(nation=classical_england_nation, user=primary_user, game=game),
            "France": Member.objects.create(nation=classical_france_nation, user=secondary_user, game=game),
            "Germany": Member.objects.create(nation=classical_germany_nation, user=tertiary_user, game=game),
            "Italy": Member.objects.create(nation=classical_italy_nation, user=primary_user, game=game),
            "Austria": Member.objects.create(nation=classical_austria_nation, user=secondary_user, game=game),
            "Russia": Member.objects.create(nation=classical_russia_nation, user=tertiary_user, game=game),
            "Turkey": Member.objects.create(nation=classical_turkey_nation, user=primary_user, game=game),
        }

        phase = Phase.objects.create(
            game=game, variant=classical_variant, season="Spring", year=1901, type="Movement", ordinal=1
        )

        setup_classical_opening(phase, members_by_nation)

        england_state = phase.phase_states.get(member=members_by_nation["England"])
        france_state = phase.phase_states.get(member=members_by_nation["France"])
        germany_state = phase.phase_states.get(member=members_by_nation["Germany"])
        italy_state = phase.phase_states.get(member=members_by_nation["Italy"])
        austria_state = phase.phase_states.get(member=members_by_nation["Austria"])
        russia_state = phase.phase_states.get(member=members_by_nation["Russia"])
        turkey_state = phase.phase_states.get(member=members_by_nation["Turkey"])

        create_order(germany_state, "mun", OrderType.MOVE, "bur")
        create_order(france_state, "par", OrderType.MOVE, "bur")

        data = adjudication_service.resolve(phase)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"

        # Check that order resolutions are correct
        mun_bounce_result = next((r for r in data["resolutions"] if r["province"] == "mun"), None)
        assert mun_bounce_result["result"] == "ErrBounce"
        assert mun_bounce_result["by"] == "par"

        par_bounce_result = next((r for r in data["resolutions"] if r["province"] == "par"), None)
        assert par_bounce_result["result"] == "ErrBounce"
        assert par_bounce_result["by"] == "mun"

    @pytest.mark.django_db
    def test_resolve_build_army_named_coast(
        self,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_italy_nation,
        classical_austria_nation,
        classical_russia_nation,
        classical_turkey_nation,
        primary_user,
        secondary_user,
        tertiary_user,
    ):
        game = Game.objects.create(variant=classical_variant, name="Classical Test Game", status=GameStatus.ACTIVE)

        members_by_nation = {
            "England": Member.objects.create(nation=classical_england_nation, user=primary_user, game=game),
            "France": Member.objects.create(nation=classical_france_nation, user=secondary_user, game=game),
            "Germany": Member.objects.create(nation=classical_germany_nation, user=tertiary_user, game=game),
            "Italy": Member.objects.create(nation=classical_italy_nation, user=primary_user, game=game),
            "Austria": Member.objects.create(nation=classical_austria_nation, user=secondary_user, game=game),
            "Russia": Member.objects.create(nation=classical_russia_nation, user=tertiary_user, game=game),
            "Turkey": Member.objects.create(nation=classical_turkey_nation, user=primary_user, game=game),
        }

        phase = Phase.objects.create(
            game=game, variant=classical_variant, season="Fall", year=1901, type="Adjustment", ordinal=3
        )

        setup_classical_opening(phase, members_by_nation)

        # Delete unit in st. petersburg
        phase.units.filter(province__province_id="stp/sc").delete()

        russia_state = phase.phase_states.get(member=members_by_nation["Russia"])

        create_order(russia_state, "stp", OrderType.BUILD, unit_type="Army")

        data = adjudication_service.resolve(phase)

        assert data["year"] == 1902
        assert data["season"] == "Spring"
        assert data["type"] == "Movement"

        # Check that order resolutions are correct
        stp_build_result = next((r for r in data["resolutions"] if r["province"] == "stp"), None)
        assert stp_build_result["result"] == "OK"
        assert stp_build_result["by"] == None

    @pytest.mark.django_db
    def test_resolve_build_fleet_named_coast(
        self,
        classical_variant,
        classical_england_nation,
        classical_france_nation,
        classical_germany_nation,
        classical_italy_nation,
        classical_austria_nation,
        classical_russia_nation,
        classical_turkey_nation,
        primary_user,
        secondary_user,
        tertiary_user,
    ):
        game = Game.objects.create(variant=classical_variant, name="Classical Test Game", status=GameStatus.ACTIVE)

        members_by_nation = {
            "England": Member.objects.create(nation=classical_england_nation, user=primary_user, game=game),
            "France": Member.objects.create(nation=classical_france_nation, user=secondary_user, game=game),
            "Germany": Member.objects.create(nation=classical_germany_nation, user=tertiary_user, game=game),
            "Italy": Member.objects.create(nation=classical_italy_nation, user=primary_user, game=game),
            "Austria": Member.objects.create(nation=classical_austria_nation, user=secondary_user, game=game),
            "Russia": Member.objects.create(nation=classical_russia_nation, user=tertiary_user, game=game),
            "Turkey": Member.objects.create(nation=classical_turkey_nation, user=primary_user, game=game),
        }

        phase = Phase.objects.create(
            game=game, variant=classical_variant, season="Fall", year=1901, type="Adjustment", ordinal=3
        )

        setup_classical_opening(phase, members_by_nation)

        # Delete unit in st. petersburg
        phase.units.filter(province__province_id="stp/sc").delete()

        russia_state = phase.phase_states.get(member=members_by_nation["Russia"])

        create_order(russia_state, "stp", OrderType.BUILD, unit_type="Fleet", named_coast="stp/nc")

        data = adjudication_service.resolve(phase)

        assert data["year"] == 1902
        assert data["season"] == "Spring"
        assert data["type"] == "Movement"

        # Check that order resolutions are correct
        stp_build_result = next((r for r in data["resolutions"] if r["province"] == "stp"), None)
        assert stp_build_result["result"] == "OK"
        assert stp_build_result["by"] == None

    @pytest.mark.django_db
    def test_resolve_move_fleet_named_coast(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Test unit move scenario with a fleet named coast.

        Italian Fleet in Mid Atlantic moves to Spain South Coast
        """
        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)

        create_unit(phase_state_italy, "mid", "Fleet")

        create_order(phase_state_italy, "mid", OrderType.MOVE, "spa", named_coast="spa/nc")

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Fleet", "nation": "Italy", "province": "spa/nc", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "mid", "result": "OK", "by": None},
            ]
        )

    @pytest.mark.django_db
    def test_resolve_move_army_named_coast(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Test unit move scenario with a army named coast.

        Italian Fleet in Mid Atlantic moves to Spain South Coast
        """
        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)

        create_unit(phase_state_italy, "mar", "Army")

        create_order(phase_state_italy, "mar", OrderType.MOVE, "spa")

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Retreat"

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "spa", "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "mar", "result": "OK", "by": None},
            ]
        )
