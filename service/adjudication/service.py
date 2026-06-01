"""In-process adjudication entry points.

`start(phase)` bootstraps a freshly-created phase: enumerates legal orders
and reports the phase's current units / supply centers (no orders to
resolve yet).

`resolve(phase)` runs the Python adjudicator against the phase's current
state and returns the dict shape `Phase.objects.create_from_adjudication_data`
consumes: next-phase descriptor + options, post-resolution units / supply
centers, and per-order resolutions (with a "by" province pointing at the
opponent that caused a bounce or cut where applicable).

Both functions emit the legacy godip-style dict so downstream consumers
(`Game.start`, `create_from_adjudication_data`, `transform_options`) keep
working unchanged.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from opentelemetry import trace

from adjudicator.domain import State, Variant
from adjudicator.engine import Engine
from adjudicator.options import get_options
from adjudicator.serializers import deserialize_game_state, deserialize_variant
from phase.utils import phase_to_canonical_game_state
from variant.utils import variant_to_canonical_dict

from .options_adapter import python_options_to_godip_dict

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


# Map the Python engine's resolution statuses back to godip's wire-format
# strings. Downstream OrderResolution.status is a CharField with choices
# defined as the godip codes (see common.constants.OrderResolutionStatus),
# and `get_status_display` is what the frontend renders.
_STATUS_TO_GODIP = {
    "OK": "OK",
    "BOUNCE": "ErrBounce",
    "CUT": "ErrSupportBroken",
    "ILLEGAL": "ErrIllegalMove",
}


def start(phase) -> Dict[str, Any]:
    logger.info(f"Starting adjudication for phase {phase.id} of game {phase.game.id}")
    with tracer.start_as_current_span("adjudication.start") as span:
        span.set_attribute("phase.id", phase.id)
        span.set_attribute("game.id", str(phase.game.id))
        span.set_attribute("variant.id", phase.variant.id)

        state, variant = _build_state(phase)
        options = get_options(state)
        godip_options = python_options_to_godip_dict(
            options,
            state.units,
            state.supply_centers,
            variant,
            state.phase.type,
        )

        nation_name_by_id = {nation.id: nation.name for nation in variant.nations}
        return {
            "season": state.phase.season,
            "year": state.phase.year,
            "type": state.phase.type,
            "options": godip_options,
            "supply_centers": _build_supply_centers(state.supply_centers, nation_name_by_id),
            "units": _build_units([], state.units, variant, nation_name_by_id),
            "resolutions": [],
        }


def resolve(phase) -> Dict[str, Any]:
    logger.info(f"Resolving phase {phase.id} of game {phase.game.id}")
    with tracer.start_as_current_span("adjudication.resolve") as span:
        span.set_attribute("phase.id", phase.id)
        span.set_attribute("game.id", str(phase.game.id))
        span.set_attribute("variant.id", phase.variant.id)

        state, variant = _build_state(phase)
        states = Engine().adjudicate(state)
        resolved = states[0]
        next_state = states[1] if len(states) > 1 else resolved

        # Advance through phases nobody can act in (empty retreat / empty
        # adjustment) so we land on the next phase that needs player input.
        # Engine.adjudicate advances one phase per call and keeps phase
        # skipping out of scope by contract, so skipping is orchestrated
        # here. Skipped phases are never persisted -- only the final
        # interactive phase is written by create_from_adjudication_data.
        next_options = get_options(next_state) if len(states) > 1 else []
        while len(states) > 1 and not next_options:
            states = Engine().adjudicate(next_state)
            next_state = states[1] if len(states) > 1 else states[0]
            next_options = get_options(next_state) if len(states) > 1 else []

        nation_name_by_id = {nation.id: nation.name for nation in variant.nations}

        if len(states) > 1:
            godip_options = python_options_to_godip_dict(
                next_options,
                next_state.units,
                next_state.supply_centers,
                variant,
                next_state.phase.type,
            )
        else:
            godip_options = {nation.name: {} for nation in variant.nations}

        return {
            "season": next_state.phase.season,
            "year": next_state.phase.year,
            "type": next_state.phase.type,
            "options": godip_options,
            "supply_centers": _build_supply_centers(
                next_state.supply_centers, nation_name_by_id
            ),
            "units": _build_units(state.units, next_state.units, variant, nation_name_by_id),
            "resolutions": _build_resolutions(state.orders, resolved.resolutions, variant),
        }


def _build_state(phase) -> Tuple[State, Variant]:
    canonical_variant = variant_to_canonical_dict(phase.variant)
    canonical_state = phase_to_canonical_game_state(phase)
    variant = deserialize_variant(canonical_variant)
    state = deserialize_game_state(canonical_state, variant)
    return state, variant


def _build_supply_centers(
    supply_centers, nation_name_by_id: Dict[str, str]
) -> List[Dict[str, Any]]:
    return sorted(
        (
            {
                "province": sc.province,
                "nation": nation_name_by_id.get(sc.nation, sc.nation),
            }
            for sc in supply_centers
        ),
        key=lambda entry: entry["province"],
    )


def _build_units(
    pre_units,
    next_units,
    variant: Variant,
    nation_name_by_id: Dict[str, str],
) -> List[Dict[str, Any]]:
    # The Python engine records `dislodged_from` as the parent province the
    # attacker came from. godip's wire format uses the attacker unit's
    # exact location (named coast included). Look up the dislodger from
    # the pre-movement units so the location matches what downstream
    # `previous_units_by_province` lookups expect.
    pre_unit_location_by_parent: Dict[str, str] = {}
    for unit in pre_units:
        parent = variant.parent_of(unit.location)
        pre_unit_location_by_parent.setdefault(parent, unit.location)

    units_out: List[Dict[str, Any]] = []
    for unit in next_units:
        dislodged_by: Optional[str] = None
        if unit.dislodged and unit.dislodged_from:
            dislodged_by = pre_unit_location_by_parent.get(unit.dislodged_from)
        units_out.append(
            {
                "province": unit.location,
                "type": unit.type,
                "nation": nation_name_by_id.get(unit.nation, unit.nation),
                "dislodged": unit.dislodged,
                "dislodged_by": dislodged_by,
            }
        )
    return sorted(units_out, key=lambda entry: entry["province"])


def _build_resolutions(orders, resolutions, variant: Variant) -> List[Dict[str, Any]]:
    # Downstream `create_from_adjudication_data` matches resolution.province
    # against order.source.province_id. Orders carry their source as the
    # parent province (named coasts get collapsed at order creation), so
    # the resolution province must be the parent too.
    #
    # For BOUNCE/CUT statuses we also populate the "by" province — godip
    # encoded it as `ErrBounce:par` / `ErrSupportBroken:mar`. The engine
    # doesn't carry that on the Resolution, so we reconstruct it from the
    # raw orders: a bounced Move is referenced by another Move targeting
    # the same parent; a cut Support is referenced by the Move that
    # attacked the supporter's parent.
    orders_by_source_parent: Dict[str, Any] = {}
    moves_by_target_parent: Dict[str, List[Any]] = {}
    for order in orders:
        if order.source is not None:
            orders_by_source_parent.setdefault(variant.parent_of(order.source), order)
        if order.order_type in ("Move", "MoveViaConvoy") and order.target is not None:
            moves_by_target_parent.setdefault(variant.parent_of(order.target), []).append(order)

    resolutions_out: List[Dict[str, Any]] = []
    for resolution in resolutions or []:
        province_parent = variant.parent_of(resolution.province)
        godip_status = _STATUS_TO_GODIP.get(resolution.resolution, "ErrIllegalMove")
        by = _find_by_province(
            resolution.resolution,
            province_parent,
            orders_by_source_parent,
            moves_by_target_parent,
            variant,
        )
        resolutions_out.append(
            {
                "province": province_parent,
                "result": godip_status,
                "by": by,
            }
        )
    return resolutions_out


def _find_by_province(
    status: str,
    province_parent: str,
    orders_by_source_parent: Dict[str, Any],
    moves_by_target_parent: Dict[str, List[Any]],
    variant: Variant,
) -> Optional[str]:
    if status not in ("BOUNCE", "CUT"):
        return None

    order = orders_by_source_parent.get(province_parent)
    if order is None:
        return None

    if status == "BOUNCE":
        # Only Moves bounce against other Moves at the same target.
        if order.order_type not in ("Move", "MoveViaConvoy") or order.target is None:
            return None
        target_parent = variant.parent_of(order.target)
        for other in moves_by_target_parent.get(target_parent, []):
            if other is order or other.source is None:
                continue
            return variant.parent_of(other.source)
        return None

    # status == "CUT": find the Move that attacked the supporter's source.
    for other in moves_by_target_parent.get(province_parent, []):
        if other.source is None:
            continue
        return variant.parent_of(other.source)
    return None
