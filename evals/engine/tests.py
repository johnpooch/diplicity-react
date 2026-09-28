import pytest

from engine.exceptions import UnknownVariantError
from engine.positions import Board
from engine.rules import legal_options, load_variant, resolve


def _opening():
    variant = load_variant("classical")
    return variant, variant["initialState"]


def _moves(options, source):
    return {option["target"] for option in options if option["source"] == source and option["orderType"] == "Move"}


class TestLegalOptions:

    def test_opening_lists_options_for_every_unit(self):
        variant, state = _opening()
        sources = {option["source"] for option in legal_options(variant, state)}
        assert sources == {unit["location"] for unit in state["units"]}

    def test_opening_moves_follow_adjacency(self):
        variant, state = _opening()
        assert _moves(legal_options(variant, state), "par") == {"bre", "bur", "gas", "pic"}

    def test_unknown_variant_raises(self):
        with pytest.raises(UnknownVariantError):
            load_variant("nonexistent")


class TestResolve:

    def test_unopposed_move_succeeds(self):
        variant, state = _opening()
        orders = [{"nation": "france", "source": "par", "orderType": "Move", "target": "bur"}]
        resolved, following = resolve(variant, {**state, "orders": orders})
        locations = {unit["location"] for unit in following["units"] if unit["nation"] == "france"}
        assert "bur" in locations and "par" not in locations

    def test_movement_advances_one_phase_to_retreat(self):
        variant, state = _opening()
        _, following = resolve(variant, state)
        assert following["phase"] == {"season": "Spring", "year": 1901, "type": "Retreat"}

    def test_bounce_leaves_both_units_in_place(self):
        variant, state = _opening()
        orders = [
            {"nation": "germany", "source": "mun", "orderType": "Move", "target": "bur"},
            {"nation": "france", "source": "par", "orderType": "Move", "target": "bur"},
        ]
        _, following = resolve(variant, {**state, "orders": orders})
        locations = {unit["location"] for unit in following["units"]}
        assert {"mun", "par"} <= locations and "bur" not in locations


SPRING_MOVEMENT = {"season": "Spring", "year": 1902, "type": "Movement"}


class TestBoard:

    def _board(self):
        return Board(load_variant("classical"))

    def test_move_to_a_named_coast_names_the_province_and_the_coast(self):
        board = self._board()
        state = board.game_state(SPRING_MOVEMENT, [{"type": "Fleet", "nation": "France", "province": "mid"}], [])
        options = board.options_by_nation(state)["France"]
        assert {"source": "mid", "order_type": "Move", "target": "spa", "named_coast": "spa/nc"} in options
        assert {"source": "mid", "order_type": "Move", "target": "spa", "named_coast": "spa/sc"} in options

    def test_unit_on_a_named_coast_is_ordered_from_its_province(self):
        board = self._board()
        state = board.game_state(SPRING_MOVEMENT, [{"type": "Fleet", "nation": "Russia", "province": "stp/sc"}], [])
        assert {option["source"] for option in board.options_by_nation(state)["Russia"]} == {"stp"}

    def test_build_at_a_two_coast_centre_offers_an_army_and_each_coast(self):
        board = self._board()
        state = board.game_state(
            {"season": "Fall", "year": 1901, "type": "Adjustment"},
            [{"type": "Army", "nation": "Russia", "province": "mos"}],
            [{"nation": "Russia", "province": "stp"}, {"nation": "Russia", "province": "mos"}],
        )
        builds = [option for option in board.options_by_nation(state)["Russia"] if option["source"] == "stp"]
        assert builds == [
            {"source": "stp", "order_type": "Build", "unit_type": "Army"},
            {"source": "stp", "order_type": "Build", "unit_type": "Fleet", "named_coast": "stp/nc"},
            {"source": "stp", "order_type": "Build", "unit_type": "Fleet", "named_coast": "stp/sc"},
        ]

    def test_retreat_is_offered_as_a_move_to_the_dislodged_unit_only(self):
        board = self._board()
        state = board.game_state(
            {"season": "Spring", "year": 1902, "type": "Retreat"},
            [
                {"type": "Army", "nation": "Germany", "province": "bur"},
                {"type": "Army", "nation": "France", "province": "bur", "dislodged": True, "dislodged_from": "mun"},
            ],
            [],
        )
        options = board.options_by_nation(state)
        assert list(options) == ["France"]
        assert {option["order_type"] for option in options["France"]} == {"Move", "Disband"}
        assert {"source": "bur", "order_type": "Move", "target": "mun"} not in options["France"]

    def test_order_to_a_named_coast_targets_the_coast(self):
        order = {"source": "mid", "order_type": "Move", "target": "spa", "named_coast": "spa/nc"}
        raw = self._board().raw_orders("Movement", {"France": [order]})
        assert raw[0]["target"] == "spa/nc" and raw[0]["nation"] == "france"

    def test_build_on_a_named_coast_is_placed_on_the_coast(self):
        order = {"source": "stp", "order_type": "Build", "unit_type": "Fleet", "named_coast": "stp/sc"}
        assert self._board().raw_orders("Adjustment", {"Russia": [order]})[0]["source"] == "stp/sc"

    def test_move_via_convoy_is_a_move_marked_as_convoyed(self):
        order = {"source": "lon", "order_type": "MoveViaConvoy", "target": "bre"}
        raw = self._board().raw_orders("Movement", {"England": [order]})[0]
        assert (raw["orderType"], raw["viaConvoy"]) == ("Move", True)

    def test_move_in_a_retreat_phase_is_a_retreat(self):
        order = {"source": "bur", "order_type": "Move", "target": "par"}
        assert self._board().raw_orders("Retreat", {"France": [order]})[0]["orderType"] == "Retreat"
