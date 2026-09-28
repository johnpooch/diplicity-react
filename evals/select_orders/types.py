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


class Fixture(TypedDict):
    id: str
    provenance: Provenance
    notes: NotRequired[str]
    variant: str
    nation: str
    phase: Phase
    units: NotRequired[list[FixtureUnit]]
    supply_centers: NotRequired[list[FixtureSupplyCenter]]
    max_orders: NotRequired[int | None]
    order_options: NotRequired[list[FixtureOrderOption]]
    ranked_options: NotRequired[RankedOptions]
