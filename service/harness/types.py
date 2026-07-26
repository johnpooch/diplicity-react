from typing import NotRequired, TypedDict

from harness.generated.api import (
    Channel as ApiChannel,
    FlatOrderOption,
    Member as ApiMember,
    PhaseState as ApiPhaseState,
    SupplyCenter as ApiSupplyCenter,
    Unit as ApiUnit,
    VariantProvince as ApiVariantProvince,
)


class ApiGame(TypedDict):
    variant_id: str
    current_phase_id: int | None
    members: list[ApiMember]


class ApiPhase(TypedDict):
    season: str
    year: int
    name: str
    type: str
    units: list[ApiUnit]
    supply_centers: list[ApiSupplyCenter]


class ApiVariant(TypedDict):
    id: str
    name: str
    provinces: list[ApiVariantProvince]


class ApiData(TypedDict):
    game: ApiGame
    phase: ApiPhase
    phase_states: list[ApiPhaseState]
    orders: list[FlatOrderOption]
    variant: ApiVariant
    channels: NotRequired[list[ApiChannel]]


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


class Persona(TypedDict):
    disposition: str
    voice: str


class ChatMessage(TypedDict):
    sender: str
    body: str


class Channel(TypedDict):
    id: int
    name: str
    private: bool
    messages: list[ChatMessage]


class Context(TypedDict):
    members: list[Member]
    phase: Phase
    max_orders: int | None
    provinces: list[Province]
    units: list[Unit]
    supply_centers: list[SupplyCenter]
    order_options: list[OrderOption]
    channels: list[Channel]


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


class Fixture(TypedDict):
    id: str
    notes: NotRequired[str]
    variant: str
    nation: str
    phase: Phase
    units: NotRequired[list[FixtureUnit]]
    supply_centers: NotRequired[list[FixtureSupplyCenter]]


class SelectOrdersFixture(Fixture):
    max_orders: NotRequired[int | None]
    order_options: NotRequired[list[FixtureOrderOption]]
    ranked_options: NotRequired[RankedOptions]
