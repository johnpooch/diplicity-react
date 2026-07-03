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


class NationDict(TypedDict, total=False):
    nation_id: str
    name: str


class ChatSenderDict(TypedDict, total=False):
    name: str
    is_current_user: bool
    nation: NationDict


class ChatMessageDict(TypedDict, total=False):
    id: int
    body: str
    sender: ChatSenderDict


class ChannelDict(TypedDict, total=False):
    id: int
    name: str
    private: bool
    messages: list[ChatMessageDict]


class ProvinceDict(TypedDict, total=False):
    id: str
    name: str


class UnitDict(TypedDict, total=False):
    type: str
    nation: NationDict
    province: ProvinceDict
    dislodged: bool


# Functional syntax because "pass" is a Python keyword.
AdjacencyDict = TypedDict("AdjacencyDict", {"to": str, "pass": str})


class VariantProvinceDict(TypedDict, total=False):
    id: str
    name: str
    type: str
    supply_center: bool
    parent_id: str | None
    adjacencies: list[AdjacencyDict]


class VariantDict(TypedDict, total=False):
    id: str
    name: str
    provinces: list[VariantProvinceDict]


class SupplyCenterDict(TypedDict, total=False):
    province: ProvinceDict
    nation: NationDict


class PhaseDict(TypedDict, total=False):
    name: str
    type: str
    units: list[UnitDict]
    supply_centers: list[SupplyCenterDict]


class ContextData(TypedDict):
    orders: list[OrderOptionDict]
    phase_states: list[dict]
    game: dict
    phase: PhaseDict
    channels: list[ChannelDict]
    variant: VariantDict
