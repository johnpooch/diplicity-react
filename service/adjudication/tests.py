import pytest
from phase.models import Phase
from game.models import Game
from member.models import Member
import adjudication.service as adjudication_service
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
        phase.units.create(
            nation=classical_england_nation,
            province=classical_edinburgh_province,
            type=UnitType.FLEET,
        )

        data = adjudication_service.start(phase)

        assert data["year"] == 1901
        assert data["season"] == "Spring"
        assert data["type"] == "Movement"
        assert data["resolutions"] == []
        assert {"nation": "England", "province": "edi"} in data["supply_centers"]
        assert {
            "dislodged": False,
            "dislodged_by": None,
            "type": "Fleet",
            "nation": "England",
            "province": "edi",
        } in data["units"]
        # Options are keyed by nation name and include an entry for each
        # variant nation, even those without units this phase.
        assert set(data["options"].keys()) == {
            nation.name for nation in classical_variant.nations.all()
        }
        # England's Fleet at Edinburgh has at least Hold as a legal order.
        assert "Hold" in data["options"]["England"]["edi"]["Next"]

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
        # Spring 1901 dislodges no one, so the empty Spring Retreat is skipped
        # and resolve() returns the next interactive phase: Fall Movement.
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"
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
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "pru", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged": False, "dislodged_by": None},
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
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "pru", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged": False, "dislodged_by": None},
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
        # Fall 1901 captures Greece and Warsaw but dislodges no one, so the
        # empty Fall Retreat is skipped and resolve() advances to the Fall
        # Adjustment, where both powers can build. Supply-center ownership is
        # recomputed during the skipped retreat, so the captured centers
        # appear here.
        assert data["season"] == "Fall"
        assert data["type"] == "Adjustment"

        assert len(data["options"]) == 2
        assert data["options"]["Italy"] != {}
        assert data["options"]["Germany"] != {}

        assert sort_by_province(data["supply_centers"]) == sort_by_province(
            [
                {"province": "ven", "nation": "Italy"},
                {"province": "rom", "nation": "Italy"},
                {"province": "nap", "nation": "Italy"},
                {"province": "gre", "nation": "Italy"},
                {"province": "tri", "nation": "Italy"},
                {"province": "kie", "nation": "Germany"},
                {"province": "ber", "nation": "Germany"},
                {"province": "mun", "nation": "Germany"},
                {"province": "den", "nation": "Germany"},
                {"province": "war", "nation": "Germany"},
            ]
        )

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged": False, "dislodged_by": None},
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
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged": False, "dislodged_by": None},
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
                {"type": "Army", "nation": "Italy", "province": "tri", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "gre", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "ion", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "rom", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "den", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "war", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ruh", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": False, "dislodged_by": None},
                {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
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
                {"type": "Army", "nation": "Italy", "province": "kie", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Italy", "province": "mun", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "kie", "dislodged": True, "dislodged_by": "ber"},
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
                {"type": "Army", "nation": "Italy", "province": "ber", "dislodged": False, "dislodged_by": None},
                {"type": "Army", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
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
        # The bounce dislodges no one, so the empty Spring Retreat is skipped
        # and resolve() returns Fall Movement. The bounce resolutions below
        # still come from the resolved Spring Movement.
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"

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
        # No dislodgement, so the empty Spring Retreat is skipped and resolve()
        # returns Fall Movement with the moved unit carried forward.
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Fleet", "nation": "Italy", "province": "spa/nc", "dislodged": False, "dislodged_by": None},
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
        # No dislodgement, so the empty Spring Retreat is skipped and resolve()
        # returns Fall Movement with the moved unit carried forward.
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"

        assert sort_by_province(data["units"]) == sort_by_province(
            [
                {"type": "Army", "nation": "Italy", "province": "spa", "dislodged": False, "dislodged_by": None},
            ]
        )

        assert sort_by_province(data["resolutions"]) == sort_by_province(
            [
                {"province": "mar", "result": "OK", "by": None},
            ]
        )


    @pytest.mark.django_db
    def test_resolve_cd_retreat_phase_is_skipped(
        self,
        phase_spring_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        When the only nation with retreat orders is in Civil Disorder, the
        Retreat phase is skipped: resolve() returns the next interactive
        phase (Fall Movement) and the dislodged unit is removed from the board.

        Italian Army Berlin moves to Kiel (supported by Munich).
        German Fleet Kiel holds — dislodged, but Germany is in Civil Disorder.
        """
        member_germany.civil_disorder = True
        member_germany.save()

        phase_state_italy = phase_spring_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_spring_1901_movement.phase_states.create(member=member_germany)

        create_supply_center(phase_state_italy, "ber")
        create_supply_center(phase_state_italy, "mun")
        create_supply_center(phase_state_germany, "kie")

        create_unit(phase_state_italy, "ber", "Army")
        create_unit(phase_state_italy, "mun", "Army")
        create_unit(phase_state_germany, "kie", "Fleet")

        create_order(phase_state_italy, "ber", OrderType.MOVE, "kie")
        create_order(phase_state_italy, "mun", OrderType.SUPPORT, "kie", "ber")

        data = adjudication_service.resolve(phase_spring_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Fall"
        assert data["type"] == "Movement"

        # The dislodged German fleet was disbanded automatically — no Germany
        # units remain on the board going into Fall Movement.
        germany_units = [u for u in data["units"] if u["nation"] == "Germany"]
        assert germany_units == []

    @pytest.mark.django_db
    def test_adjustment_not_skipped_when_cd_nation_disbands_and_other_nation_builds(
        self,
        phase_fall_1901_movement,
        member_italy,
        member_germany,
    ):
        """
        Regression: when a CD nation needs to disband and a non-CD nation needs
        to build, the Adjustment phase must not be skipped.

        Build options have source = empty SC province (not a unit location), so
        they were invisible to _should_skip's location_to_nation lookup. Only
        Germany's disband option was detected; since Germany is the only nation
        in option_nations and is in cd_nations, the phase was incorrectly
        skipped, cheating Italy out of a build.

        Setup:
        - Italy holds at ven (home SC); also owns rom (empty home SC).
          1 unit, 2 SCs → needs to build 1 at rom.
        - Germany (Civil Disorder) holds at kie (home SC) and ruh (non-SC).
          2 units, 1 SC → needs to disband 1 (auto-handled by CD).
        No dislodgements → empty Fall Retreat is skipped automatically.
        The Adjustment phase must still be created for Italy's build.
        """
        member_germany.civil_disorder = True
        member_germany.save()

        phase_state_italy = phase_fall_1901_movement.phase_states.create(member=member_italy)
        phase_state_germany = phase_fall_1901_movement.phase_states.create(member=member_germany)

        # Italy: 1 unit at ven, owns ven + rom (both Italy home SCs). rom is empty.
        create_supply_center(phase_state_italy, "ven")
        create_supply_center(phase_state_italy, "rom")
        create_unit(phase_state_italy, "ven", "Army")

        # Germany: 2 units (kie home SC + ruh non-SC), 1 SC (kie). Surplus = 1 disband.
        create_supply_center(phase_state_germany, "kie")
        create_unit(phase_state_germany, "kie", "Army")
        create_unit(phase_state_germany, "ruh", "Army")

        data = adjudication_service.resolve(phase_fall_1901_movement)

        assert data["year"] == 1901
        assert data["season"] == "Fall"
        assert data["type"] == "Adjustment"

        italy_options = data["options"].get("Italy", {})
        assert italy_options != {}, "Italy must have build options in the Adjustment phase"


class TestUserUploadedVariant:
    """Regression: prior to dropping the godip HTTP adjudicator, creating a
    sandbox game with a freshly-uploaded variant (any id godip doesn't ship
    with) failed at ``Game.start`` because the start-with-options request
    404'd at godip-adjudication.appspot.com. With the in-process Python
    adjudicator there is no per-variant gate."""

    @pytest.mark.django_db
    def test_create_sandbox_with_user_uploaded_variant(
        self, primary_user, classical_variant
    ):
        import copy

        from variant.utils import (
            create_variant_from_dvar,
            variant_to_canonical_dict,
        )
        from common.constants import GameStatus, PhaseStatus

        dvar = copy.deepcopy(variant_to_canonical_dict(classical_variant))
        dvar["id"] = "user-uploaded-variant"
        dvar["name"] = "User Uploaded Variant"
        variant = create_variant_from_dvar(dvar, owner=primary_user)

        game = Game.objects.create_sandbox(
            user=primary_user,
            name="Sandbox With User Variant",
            variant=variant,
        )

        assert game.status == GameStatus.ACTIVE
        current_phase = game.current_phase
        assert current_phase is not None
        assert current_phase.status == PhaseStatus.ACTIVE
        # Options dict is populated for every nation in the variant.
        assert set(current_phase.options.keys()) == {
            nation.name for nation in variant.nations.all()
        }
