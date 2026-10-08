from typing import NotRequired, TypedDict


class Member(TypedDict):
    name: str
    nation: str
    is_current_user: bool


class Phase(TypedDict):
    season: str
    year: int
    type: str


class Adjacency(TypedDict):
    to: str
    allows: list[str]


class Province(TypedDict):
    id: str
    name: str
    type: str
    supply_center: bool
    parent_id: str | None
    adjacencies: list[Adjacency]


class Unit(TypedDict):
    type: str
    nation: str
    province: str
    dislodged: bool


class SupplyCenter(TypedDict):
    nation: str | None
    province: str


class OrderOption(TypedDict):
    source: str
    order_type: str
    target: str | None
    aux: str | None
    unit_type: str | None
    named_coast: str | None


class Context(TypedDict):
    members: list[Member]
    phase: Phase
    max_orders: int | None
    provinces: list[Province]
    units: list[Unit]
    supply_centers: list[SupplyCenter]
    order_options: list[OrderOption]


class FixtureUnit(TypedDict):
    type: str
    nation: str
    province: str
    dislodged: NotRequired[bool]
    dislodged_from: NotRequired[str]


class FixtureSupplyCenter(TypedDict):
    nation: str
    province: str


class FixtureOrderOption(TypedDict):
    source: str
    order_type: str
    target: NotRequired[str | None]
    aux: NotRequired[str | None]
    unit_type: NotRequired[str | None]
    named_coast: NotRequired[str | None]


class RankedOptions(TypedDict):
    good: list[FixtureOrderOption]
    neutral: list[FixtureOrderOption]
    bad: list[FixtureOrderOption]


class Provenance(TypedDict):
    source: str
    game_id: NotRequired[str]
    phase_id: NotRequired[int]
    phase_ordinal: NotRequired[int]
    harvested_at: NotRequired[str]
    press_type: NotRequired[str]
    was_bot: NotRequired[bool]


class OrderResolution(TypedDict):
    nation: str
    source: str
    result: str


class Outcome(TypedDict):
    resolutions: list[OrderResolution]
    units: list[FixtureUnit]
    supply_centers: list[FixtureSupplyCenter]


class OptionLabel(TypedDict):
    options: list[str]
    label: str
    labeller: str
    labelled_at: str
    note: NotRequired[str]


class OrderSetLabel(TypedDict):
    orders: list[str]
    label: str
    labeller: str
    labelled_at: str
    reason: NotRequired[str]


class Discarded(TypedDict):
    by: str
    at: str
    reason: str


class Fixture(TypedDict):
    schema_version: int
    id: str
    provenance: Provenance
    notes: NotRequired[str]
    variant: str
    nation: str
    phase: Phase
    units: NotRequired[list[FixtureUnit]]
    supply_centers: NotRequired[list[FixtureSupplyCenter]]
    contested_provinces: NotRequired[list[str]]
    max_orders: NotRequired[int | None]
    order_options: NotRequired[list[FixtureOrderOption]]
    decision_richness: NotRequired[int]
    actual_orders: NotRequired[dict[str, list[FixtureOrderOption]]]
    actual_outcome: NotRequired[Outcome]
    ranked_options: NotRequired[RankedOptions]
    option_labels: NotRequired[list[OptionLabel]]
    order_set_labels: NotRequired[list[OrderSetLabel]]
    eval_sets: list[str]
    discarded: NotRequired[Discarded]
