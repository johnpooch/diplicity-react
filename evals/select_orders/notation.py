from select_orders.constants import PhaseType
from select_orders.types import Context, OrderOption

DASH = "–"
SEPARATOR = " · "


def _parent(province_id: str) -> str:
    return province_id.split("/")[0]


class Notation:
    def __init__(self, context: Context):
        self.provinces = {province["id"]: province for province in context["provinces"]}
        retreat = context["phase"]["type"] == PhaseType.RETREAT
        units = sorted(context.get("units", []), key=lambda unit: unit["dislodged"] == retreat)
        self.letters = {_parent(unit["province"]): unit["type"][0] for unit in units}

    def province(self, province_id: str) -> str:
        province = self.provinces.get(province_id)
        if province is None:
            return province_id
        if province["parent_id"]:
            return self.province(province["parent_id"]) + province_id.removeprefix(province["parent_id"])
        return province_id.upper() if province["type"] == "sea" else province_id.capitalize()

    def unit(self, province_id: str) -> str:
        letter = self.letters.get(_parent(province_id))
        return f"{letter} {self.province(province_id)}" if letter else self.province(province_id)

    def order(self, option: OrderOption) -> str:
        source = self.unit(option["source"])
        order_type = option["order_type"]
        target = option["named_coast"] or option["target"]
        if order_type == "Hold":
            return f"{source} H"
        if order_type == "Move":
            return f"{source}{DASH}{self.province(target)}"
        if order_type == "MoveViaConvoy":
            return f"{source}{DASH}{self.province(target)} via convoy"
        if order_type == "Support":
            supported = self.unit(option["aux"])
            if option["target"] in (None, option["aux"]):
                return f"{source} S {supported}"
            return f"{source} S {supported}{DASH}{self.province(option['target'])}"
        if order_type == "Convoy":
            return f"{source} C {self.unit(option['aux'])}{DASH}{self.province(target)}"
        if order_type == "Build":
            return f"Build {option['unit_type'][0]} {self.province(option['named_coast'] or option['source'])}"
        return f"{order_type} {source}"

    def order_set(self, options: list[OrderOption]) -> str:
        ordered = sorted(options, key=lambda option: option["source"])
        return SEPARATOR.join(self.order(option) for option in ordered)
