import pytest

from engine.exceptions import UnknownVariantError
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
