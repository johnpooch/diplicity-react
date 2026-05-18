"""Normalized adjudication comparison for shadow mode.

The godip adjudicator and the Python adjudicator describe the same outcome
in different shapes and vocabularies. `CanonicalAdjudication` is the common
form both are reduced to; `diff_canonical` compares two of them and assigns
a severity tier to any mismatch.
"""
from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

from phase.utils import transform_options


TIER_1 = "tier_1"
TIER_2 = "tier_2"
TIER_3 = "tier_3"

_TIER_RANK = {TIER_1: 1, TIER_2: 2, TIER_3: 3}

# godip names resolution statuses differently from the Python engine
# (adjudicator.types.Status). Without this mapping every comparison would
# report a tier-2 diff purely from the vocabulary difference.
_GODIP_STATUS_MAP = {
    "OK": "OK",
    "ErrBounce": "BOUNCE",
    "ErrSupportBroken": "CUT",
}


def _canonical_status(godip_status):
    if godip_status in _GODIP_STATUS_MAP:
        return _GODIP_STATUS_MAP[godip_status]
    if godip_status.startswith("Err"):
        return "ILLEGAL"
    return godip_status


def _is_named_coast_dict(data):
    return bool(data) and all("/" in key for key in data)


# Option tuple: (nation, order_type, source, target, aux, unit_type).
OptionTuple = Tuple[str, str, Optional[str], Optional[str], Optional[str], Optional[str]]


@dataclass(frozen=True)
class CanonicalAdjudication:
    next_phase: Tuple[str, int, str]
    units: FrozenSet[Tuple[str, str, str, bool]]
    dislodger_pairs: FrozenSet[Tuple[str, str]]
    supply_centers: FrozenSet[Tuple[str, str]]
    resolution_statuses: FrozenSet[Tuple[str, str]]
    options_by_nation: FrozenSet[OptionTuple]


@dataclass(frozen=True)
class FieldDiff:
    field: str
    tier: str
    only_in_godip: Tuple
    only_in_python: Tuple


@dataclass(frozen=True)
class StructuredDiff:
    tier: Optional[str]
    field_diffs: Tuple[FieldDiff, ...]

    @property
    def matched(self) -> bool:
        return self.tier is None

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "fields": [
                {
                    "field": field_diff.field,
                    "tier": field_diff.tier,
                    "only_in_godip": [list(item) for item in field_diff.only_in_godip],
                    "only_in_python": [list(item) for item in field_diff.only_in_python],
                }
                for field_diff in self.field_diffs
            ],
        }


# === godip normalizer ===


def _flatten_godip_options(raw_options, phase_type) -> FrozenSet[OptionTuple]:
    transformed = transform_options(raw_options)
    tuples = set()
    for nation, sources in transformed.items():
        for source, order_types in sources.items():
            for order_type, data in order_types.items():
                tuples.update(
                    _godip_option_tuples(nation, source, order_type, data, phase_type)
                )
    return frozenset(tuples)


def _godip_option_tuples(nation, source, order_type, data, phase_type):
    if order_type in ("Hold", "Disband"):
        return [(nation, order_type, source, None, None, None)]

    if order_type in ("Move", "MoveViaConvoy"):
        normalized = "Retreat" if phase_type == "Retreat" else "Move"
        tuples = []
        for target, target_data in data.items():
            if _is_named_coast_dict(target_data):
                for coast in target_data:
                    tuples.append((nation, normalized, source, coast, None, None))
            else:
                tuples.append((nation, normalized, source, target, None, None))
        return tuples

    if order_type in ("Support", "Convoy"):
        return [
            (nation, order_type, source, target, aux, None)
            for aux, aux_data in data.items()
            for target in aux_data
        ]

    if order_type == "Build":
        tuples = []
        for unit_type, unit_type_data in data.items():
            if _is_named_coast_dict(unit_type_data):
                for coast in unit_type_data:
                    tuples.append((nation, "Build", coast, coast, None, unit_type))
            else:
                tuples.append((nation, "Build", source, source, None, unit_type))
        return tuples

    return []


def canonicalize_godip_response(validated_data) -> CanonicalAdjudication:
    units = validated_data["units"]
    return CanonicalAdjudication(
        next_phase=(
            validated_data["season"],
            validated_data["year"],
            validated_data["type"],
        ),
        units=frozenset(
            (unit["nation"], unit["type"], unit["province"], bool(unit["dislodged"]))
            for unit in units
        ),
        dislodger_pairs=frozenset(
            (unit["province"], unit["dislodged_by"])
            for unit in units
            if unit["dislodged"] and unit["dislodged_by"]
        ),
        supply_centers=frozenset(
            (supply_center["nation"], supply_center["province"])
            for supply_center in validated_data["supply_centers"]
        ),
        resolution_statuses=frozenset(
            (resolution["province"], _canonical_status(resolution["result"]))
            for resolution in validated_data["resolutions"]
        ),
        options_by_nation=_flatten_godip_options(
            validated_data["options"], validated_data["type"]
        ),
    )


# === Python normalizer ===


def canonicalize_python_response(states, options) -> CanonicalAdjudication:
    resolved = states[0]
    final = states[-1]
    name_of = {nation.id: nation.name for nation in final.variant.nations}

    standing_nation_by_location = {
        unit.location: unit.nation for unit in final.units if not unit.dislodged
    }
    dislodged_nation_by_location = {
        unit.location: unit.nation for unit in final.units if unit.dislodged
    }
    sc_nation_by_province = {
        supply_center.province: supply_center.nation
        for supply_center in final.supply_centers
    }

    # In a Retreat phase godip reports resolutions only for submitted orders;
    # a dislodged unit given no order is disbanded without a resolution entry.
    # The Python engine resolves an inferred default Disband for it, so filter
    # those out to match godip.
    resolved_is_retreat = resolved.phase.type == "Retreat"
    ordered_provinces = {
        final.variant.parent_of(order.source) for order in resolved.orders
    }

    # Retreat-phase options belong to the dislodged units. A standing unit
    # (the dislodger) can occupy the same province as the unit it dislodged,
    # so it must not shadow the dislodged unit's nation.
    is_retreat_phase = final.phase.type == "Retreat"
    options_by_nation = set()
    for option in options:
        if is_retreat_phase:
            nation_id = dislodged_nation_by_location.get(option.source)
        else:
            nation_id = standing_nation_by_location.get(option.source)
            if nation_id is None:
                parent = final.variant.parent_of(option.source)
                nation_id = sc_nation_by_province.get(parent)
        if nation_id is None:
            continue
        # godip keys an existing unit's options by its parent province even
        # when the unit sits on a named coast; only Build options carry the
        # coast itself. Normalize Python's source to match.
        if option.order_type == "Build":
            option_source = option.source
        else:
            option_source = final.variant.parent_of(option.source)
        options_by_nation.add(
            (
                name_of.get(nation_id, nation_id),
                option.order_type,
                option_source,
                option.target,
                option.aux,
                option.unit_type,
            )
        )

    return CanonicalAdjudication(
        next_phase=(final.phase.season, final.phase.year, final.phase.type),
        units=frozenset(
            (name_of.get(unit.nation, unit.nation), unit.type, unit.location, unit.dislodged)
            for unit in final.units
        ),
        dislodger_pairs=frozenset(
            (unit.location, unit.dislodged_from)
            for unit in final.units
            if unit.dislodged and unit.dislodged_from
        ),
        supply_centers=frozenset(
            (name_of.get(sc.nation, sc.nation), sc.province)
            for sc in final.supply_centers
        ),
        resolution_statuses=frozenset(
            (final.variant.parent_of(resolution.province), resolution.resolution)
            for resolution in (resolved.resolutions or [])
            if not resolved_is_retreat
            or final.variant.parent_of(resolution.province) in ordered_provinces
        ),
        options_by_nation=frozenset(options_by_nation),
    )


# === diff ===


_SET_FIELDS = (
    ("units", TIER_1),
    ("supply_centers", TIER_1),
    ("dislodger_pairs", TIER_1),
    ("resolution_statuses", TIER_2),
    ("options_by_nation", TIER_3),
)


def diff_canonical(godip: CanonicalAdjudication, python: CanonicalAdjudication) -> StructuredDiff:
    field_diffs = []

    if godip.next_phase != python.next_phase:
        field_diffs.append(
            FieldDiff(
                field="next_phase",
                tier=TIER_1,
                only_in_godip=(tuple(godip.next_phase),),
                only_in_python=(tuple(python.next_phase),),
            )
        )

    for field, tier in _SET_FIELDS:
        godip_set = getattr(godip, field)
        python_set = getattr(python, field)
        only_in_godip = godip_set - python_set
        only_in_python = python_set - godip_set
        if only_in_godip or only_in_python:
            field_diffs.append(
                FieldDiff(
                    field=field,
                    tier=tier,
                    only_in_godip=tuple(sorted(only_in_godip)),
                    only_in_python=tuple(sorted(only_in_python)),
                )
            )

    if not field_diffs:
        return StructuredDiff(tier=None, field_diffs=())

    tier = min((field_diff.tier for field_diff in field_diffs), key=_TIER_RANK.get)
    return StructuredDiff(tier=tier, field_diffs=tuple(field_diffs))
