from typing import TypedDict


class FieldDict(TypedDict):
    id: str
    label: str


class OrderOptionDict(TypedDict, total=False):
    source: FieldDict
    order_type: FieldDict
    target: FieldDict
    aux: FieldDict
    unit_type: FieldDict
    named_coast: FieldDict


class ChatSenderDict(TypedDict, total=False):
    name: str
    is_current_user: bool


class ChatMessageDict(TypedDict, total=False):
    id: int
    body: str
    sender: ChatSenderDict


class ChannelDict(TypedDict, total=False):
    id: int
    name: str
    private: bool
    messages: list[ChatMessageDict]


class ContextData(TypedDict):
    orders: list[OrderOptionDict]
    phase_states: list[dict]
    game: dict
    channels: list[ChannelDict]
