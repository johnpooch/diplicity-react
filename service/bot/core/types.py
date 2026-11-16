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


class BotContext(TypedDict):
    member_id: int
    members: list[Member]
    phase: Phase
    max_orders: int | None
    provinces: list[Province]
    units: list[Unit]
    supply_centers: list[SupplyCenter]
    order_options: list[OrderOption]
    channels: list[Channel]
    nations: list[str]


class SelectionContext(TypedDict):
    channel: Channel
    candidates: list[int]


class Selection(TypedDict):
    member_id: int
    mode: str


class ConversationProposal(TypedDict):
    channel_id: int | None
    member_ids: list[int]
    topic: str
