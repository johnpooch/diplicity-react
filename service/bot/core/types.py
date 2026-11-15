from typing import TypedDict


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


class Message(TypedDict):
    sender_id: int
    body: str


class Channel(TypedDict):
    id: int
    messages: list[Message]


class OrdersContext(TypedDict):
    members: list[Member]
    phase: Phase
    max_orders: int | None
    provinces: list[Province]
    units: list[Unit]
    supply_centers: list[SupplyCenter]
    order_options: list[OrderOption]
    channels: list[Channel]


class SelectionContext(TypedDict):
    channel: Channel
    candidates: list[int]


class ResponseContext(TypedDict):
    member_id: int
    channel: Channel
    phase: Phase
    provinces: list[Province]
    units: list[Unit]
    supply_centers: list[SupplyCenter]


class LightResponseContext(TypedDict):
    member_id: int
    channel: Channel


class JournalContext(TypedDict):
    member_id: int
    phase: Phase


class PlanContext(TypedDict):
    member_id: int
    phase: Phase
    channels: list[Channel]


class DrawContext(TypedDict):
    member_id: int
    phase: Phase
    nations: list[str]


class Selection(TypedDict):
    member_id: int
    mode: str


class ConversationProposal(TypedDict):
    channel_id: int | None
    member_ids: list[int]
    topic: str
