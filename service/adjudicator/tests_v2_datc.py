"""
DATC test suite for the v2 engine.

Reuses the v1 wire-format test DSL in `tests.py` (classical variant,
StateBuilder, helpers) but routes adjudication through the v2
`Engine` via the existing wire-format serializers.

This is the v2 engine's DATC compliance harness. Tests that exercise
features explicitly out of scope for the v2 prototype (get_options,
phase skipping, supply-center transfer, solo-victory detection) are
skipped here.
"""
from __future__ import annotations

from typing import Any, Dict, List

import pytest

from . import tests as _v1_tests
from .engine_v2 import Engine as _EngineV2
from .serializers import (
    deserialize_game_state,
    deserialize_variant,
    serialize_game_state,
)

# === Tests skipped: out of v2 prototype scope ===
#
# These v1 tests exercise capabilities the v2 engine does not implement.
# They are skipped here so the DATC-adjudication signal is not polluted.
#
#   get_options            — option enumeration is out of scope
#   phase skipping         — v2 returns at most two states (resolved + next)
#   supply-center transfer — v2 does not update SC ownership
#   solo-victory detection — v2 does not set state.outcome
_OUT_OF_SCOPE: set = {
    # get_options
    "test_get_options_in_movement_phase_includes_hold_for_each_unit",
    "test_get_options_includes_legal_move_targets_for_army",
    "test_get_options_excludes_fleet_only_targets_for_army",
    "test_get_options_excludes_army_only_targets_for_fleet",
    "test_get_options_outside_movement_phase_returns_empty_list",
    "test_get_options_includes_support_for_adjacent_unit_move",
    "test_get_options_in_adjustment_phase_includes_builds_for_surplus_nation",
    "test_get_options_in_adjustment_phase_includes_disbands_for_deficit_nation",
    "test_get_options_in_adjustment_phase_excludes_occupied_home_centers",
    "test_get_options_in_adjustment_phase_returns_empty_for_balanced_nations",
    # phase skipping (asserts on result[1]/result[2] being a skipped phase)
    "test_adjudicate_with_no_orders_holds_all_units",
    "test_movement_with_no_dislodgements_skips_retreat_phase",
    "test_movement_with_dislodgement_does_not_skip_retreat_phase",
    "test_fall_movement_with_balanced_powers_skips_through_to_next_year",
    # solo-victory detection
    "test_solo_victory_after_adjustment_with_builds",
    "test_solo_victory_after_skipped_balanced_adjustment",
    "test_no_solo_outcome_when_no_nation_meets_threshold",
}


def _adjudicate_v2(variant_dict: Dict[str, Any], state_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    variant = deserialize_variant(variant_dict)
    state = deserialize_game_state(state_dict, variant)
    result = _EngineV2().adjudicate(state)
    return [serialize_game_state(s) for s in result]


def _get_options_v2(variant_dict: Dict[str, Any], state_dict: Dict[str, Any]):
    raise NotImplementedError("get_options is out of scope for the v2 prototype")


@pytest.fixture(autouse=True)
def _route_through_v2(monkeypatch):
    """Redirect tests.py's `adjudicate` / `get_options` references to v2."""
    monkeypatch.setattr(_v1_tests, "adjudicate", _adjudicate_v2)
    monkeypatch.setattr(_v1_tests, "get_options", _get_options_v2)
    yield


# === Re-export every test_* from tests.py ===

_skipped_names: set = set()
for _name in dir(_v1_tests):
    if not _name.startswith("test_"):
        continue
    if _name in _OUT_OF_SCOPE:
        _skipped_names.add(_name)
        continue
    globals()[_name] = getattr(_v1_tests, _name)
del _name
