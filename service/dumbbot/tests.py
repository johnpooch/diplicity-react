import random
from unittest.mock import patch

import pytest

from common.constants import OrderType
from harness.adapter import fixture_to_context

from dumbbot.exceptions import DumbbotError
from dumbbot.policy import select_orders


def _movement_fixture(**overrides):
    fixture = {
        "id": "movement",
        "variant": "classical",
        "nation": "England",
        "phase": {"season": "Spring", "year": 1901, "type": "Movement"},
        "units": [
            {"type": "Fleet", "nation": "England", "province": "lon"},
            {"type": "Fleet", "nation": "England", "province": "edi"},
            {"type": "Army", "nation": "England", "province": "lvp"},
        ],
        "supply_centers": [
            {"nation": "England", "province": "lon"},
            {"nation": "England", "province": "edi"},
            {"nation": "England", "province": "lvp"},
            {"nation": "France", "province": "par"},
            {"nation": "France", "province": "bre"},
            {"nation": "France", "province": "mar"},
        ],
        "order_options": [
            {"source": "lon", "order_type": "Hold"},
            {"source": "lon", "order_type": "Move", "target": "nth"},
            {"source": "lon", "order_type": "Move", "target": "eng"},
            {"source": "edi", "order_type": "Hold"},
            {"source": "edi", "order_type": "Move", "target": "nth"},
            {"source": "edi", "order_type": "Move", "target": "nrg"},
            {"source": "lvp", "order_type": "Hold"},
            {"source": "lvp", "order_type": "Move", "target": "yor"},
            {"source": "lvp", "order_type": "Move", "target": "wal"},
        ],
    }
    fixture.update(overrides)
    return fixture


class TestSelectOrders:

    def test_returns_options_by_identity(self):
        context = fixture_to_context(_movement_fixture())
        orders = select_orders(context, rng=random.Random(1))

        option_ids = {id(option) for option in context["order_options"]}
        assert orders
        assert all(id(order) in option_ids for order in orders)

    def test_at_most_one_order_per_source_and_full_coverage(self):
        context = fixture_to_context(_movement_fixture())
        orders = select_orders(context, rng=random.Random(1))

        sources = [order["source"] for order in orders]
        assert sorted(sources) == ["edi", "lon", "lvp"]

    def test_seeded_rng_is_deterministic(self):
        context = fixture_to_context(_movement_fixture())
        first = select_orders(context, rng=random.Random(42))
        second = select_orders(context, rng=random.Random(42))

        assert first == second

    def test_moves_toward_fat_undefended_enemy_center(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1901, "type": "Movement"},
            units=[{"type": "Army", "nation": "England", "province": "pic"}],
            order_options=[
                {"source": "pic", "order_type": "Hold"},
                {"source": "pic", "order_type": "Move", "target": "par"},
                {"source": "pic", "order_type": "Move", "target": "bur"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = select_orders(context, rng=random.Random(1))

        assert orders == [{
            "source": "pic",
            "order_type": OrderType.MOVE,
            "target": "par",
            "aux": None,
            "unit_type": None,
            "named_coast": None,
        }]

    def test_empty_adjacencies_still_covers_every_source(self):
        context = fixture_to_context(_movement_fixture())
        for province in context["provinces"]:
            province["adjacencies"] = []

        orders = select_orders(context, rng=random.Random(1))

        assert sorted(order["source"] for order in orders) == ["edi", "lon", "lvp"]

    def test_fleet_move_to_multi_coast_province_keeps_named_coast(self):
        fixture = _movement_fixture(
            units=[{"type": "Fleet", "nation": "England", "province": "mid"}],
            supply_centers=[
                {"nation": "France", "province": "spa"},
                {"nation": "France", "province": "par"},
                {"nation": "France", "province": "mar"},
            ],
            order_options=[
                {"source": "mid", "order_type": "Hold"},
                {"source": "mid", "order_type": "Move", "target": "spa", "named_coast": "spa/nc"},
                {"source": "mid", "order_type": "Move", "target": "spa", "named_coast": "spa/sc"},
                {"source": "mid", "order_type": "Move", "target": "nat"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = select_orders(context, rng=random.Random(1))

        assert len(orders) == 1
        assert orders[0]["target"] == "spa"
        assert orders[0]["named_coast"] in ("spa/nc", "spa/sc")

    def test_retreat_options_presented_as_moves_are_handled(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1902, "type": "Retreat"},
            nation="Austria",
            units=[
                {"type": "Army", "nation": "Austria", "province": "tri", "dislodged": True},
                {"type": "Army", "nation": "Italy", "province": "tri"},
            ],
            supply_centers=[
                {"nation": "Italy", "province": "tri"},
            ],
            order_options=[
                {"source": "tri", "order_type": "Move", "target": "ser"},
                {"source": "tri", "order_type": "Move", "target": "alb"},
                {"source": "tri", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = select_orders(context, rng=random.Random(1))

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.MOVE
        assert orders[0]["target"] == "ser"

    def test_retreat_disbands_when_every_destination_is_occupied(self):
        fixture = _movement_fixture(
            phase={"season": "Fall", "year": 1902, "type": "Retreat"},
            nation="Austria",
            units=[
                {"type": "Army", "nation": "Austria", "province": "tri", "dislodged": True},
                {"type": "Army", "nation": "Italy", "province": "tri"},
                {"type": "Army", "nation": "Italy", "province": "ser"},
                {"type": "Army", "nation": "Italy", "province": "alb"},
            ],
            supply_centers=[],
            order_options=[
                {"source": "tri", "order_type": "Move", "target": "ser"},
                {"source": "tri", "order_type": "Move", "target": "alb"},
                {"source": "tri", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        orders = select_orders(context, rng=random.Random(1))

        assert [order["order_type"] for order in orders] == [OrderType.DISBAND]

    def test_builds_respect_max_orders(self):
        fixture = _movement_fixture(
            phase={"season": "Winter", "year": 1901, "type": "Adjustment"},
            nation="Russia",
            max_orders=1,
            units=[
                {"type": "Army", "nation": "Russia", "province": "mos"},
            ],
            supply_centers=[
                {"nation": "Russia", "province": "mos"},
                {"nation": "Russia", "province": "war"},
                {"nation": "Russia", "province": "sev"},
            ],
            order_options=[
                {"source": "sev", "order_type": "Build", "unit_type": "Army"},
                {"source": "war", "order_type": "Build", "unit_type": "Army"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = select_orders(context, rng=random.Random(1))

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.BUILD
        assert orders[0]["source"] == "sev"

    def test_disbands_least_valuable_unit_up_to_max_orders(self):
        fixture = _movement_fixture(
            phase={"season": "Winter", "year": 1902, "type": "Adjustment"},
            max_orders=1,
            units=[
                {"type": "Army", "nation": "England", "province": "bur"},
                {"type": "Army", "nation": "England", "province": "wal"},
            ],
            supply_centers=[
                {"nation": "England", "province": "lon"},
                {"nation": "France", "province": "par"},
                {"nation": "France", "province": "mar"},
                {"nation": "France", "province": "bre"},
            ],
            order_options=[
                {"source": "bur", "order_type": "Disband"},
                {"source": "wal", "order_type": "Disband"},
            ],
        )
        context = fixture_to_context(fixture)

        with patch("dumbbot.policy.PLAY_ALTERNATIVE", 0):
            orders = select_orders(context, rng=random.Random(1))

        assert len(orders) == 1
        assert orders[0]["order_type"] == OrderType.DISBAND
        assert orders[0]["source"] == "wal"

    def test_raises_when_current_nation_missing(self):
        context = fixture_to_context(_movement_fixture())
        for member in context["members"]:
            member["is_current_user"] = False

        with pytest.raises(DumbbotError):
            select_orders(context, rng=random.Random(1))

    def test_empty_options_return_no_orders(self):
        context = fixture_to_context(_movement_fixture(order_options=[]))

        assert select_orders(context, rng=random.Random(1)) == []
