import json
from io import StringIO

import pytest
from django.core.management import call_command

from integration.dsl import GameSession


@pytest.mark.django_db
def test_dump_fixture_outputs_expected_shape(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    session = GameSession.start(
        variant=italy_vs_germany_variant,
        clients=[authenticated_client, authenticated_client_for_secondary_user],
    )

    # One Movement phase with one order per nation; both resolve OK.
    session.order("Germany", "kie", "Move", "den")
    session.order("Italy", "ven", "Move", "tri")
    session.confirm_all()
    session.resolve()

    # Retreat phase auto-resolves (no dislodgements).
    session.assert_phase(season="Spring", year=1901, type="Retreat")
    session.resolve()

    stdout = StringIO()
    call_command("dump_fixture", session.game.id, stdout=stdout)
    document = json.loads(stdout.getvalue())

    assert document["schema_version"] == 1
    assert document["variant"] == italy_vs_germany_variant.name
    assert document["outcome"] is None  # game still active
    assert document["source"]["captured_from"] == "database"
    assert isinstance(document["source"]["original_game_id_hash"], str)
    assert isinstance(document["source"]["captured_at"], str)
    assert isinstance(document["source"]["game_created_at"], str)
    # last_phase_completed_at may be null mid-game; test creates an active game so no final completion.
    assert "last_phase_completed_at" in document["source"]

    phases = document["phases"]
    assert len(phases) >= 3  # Spring Movement, Spring Retreat, plus the new current phase

    # Phase 1: Spring 1901 Movement, both nations confirmed.
    p1 = phases[0]
    assert (p1["ordinal"], p1["season"], p1["year"], p1["type"]) == (1, "Spring", 1901, "Movement")
    assert p1["resolution_trigger"] == "consensus"
    assert p1["non_confirming_nations"] == []

    nations_with_orders = {o["nation"] for o in p1["orders"]}
    assert nations_with_orders == {"Germany", "Italy"}
    for order in p1["orders"]:
        assert set(order.keys()) == {"nation", "selected", "expected_resolution"}
        assert isinstance(order["selected"], list)
        assert order["expected_resolution"] == "OK"

    germany_order = next(o for o in p1["orders"] if o["nation"] == "Germany")
    italy_order = next(o for o in p1["orders"] if o["nation"] == "Italy")
    assert germany_order["selected"] == ["kie", "Move", "den"]
    assert italy_order["selected"] == ["ven", "Move", "tri"]

    # expected_state_after for phase 1 = phase 2's pre-state.
    state_after_p1 = p1["expected_state_after"]
    assert state_after_p1 is not None
    units = state_after_p1["units"]
    assert {"nation", "type", "province", "dislodged"} == set(units[0].keys())
    germany_units = {(u["province"], u["type"]) for u in units if u["nation"] == "Germany"}
    italy_units = {(u["province"], u["type"]) for u in units if u["nation"] == "Italy"}
    assert ("den", "Fleet") in germany_units, germany_units
    assert ("tri", "Army") in italy_units, italy_units

    supply_centers = state_after_p1["supply_centers"]
    assert isinstance(supply_centers, dict)
    assert all(isinstance(v, str) for v in supply_centers.values())

    # Phase 2: Spring 1901 Retreat, no orders, auto-resolved.
    p2 = phases[1]
    assert (p2["season"], p2["year"], p2["type"]) == ("Spring", 1901, "Retreat")
    assert p2["resolution_trigger"] == "auto"
    assert p2["orders"] == []
    assert p2["non_confirming_nations"] == []

    # Final phase has no expected_state_after (no next phase to source from).
    assert phases[-1]["expected_state_after"] is None

    # Orders are sorted by (nation, selected) for stable diffs.
    orders_sorted = sorted(p1["orders"], key=lambda o: (o["nation"], tuple(o["selected"])))
    assert p1["orders"] == orders_sorted
