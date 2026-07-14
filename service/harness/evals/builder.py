from harness.types import ContextData


def field(value):
    return {"id": value, "label": value} if value is not None else None


def option(source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
    return {
        "source": field(source),
        "order_type": field(order_type),
        "target": field(target),
        "aux": field(aux),
        "unit_type": field(unit_type),
        "named_coast": field(named_coast),
    }


def nation(name):
    return {"nation_id": name.lower(), "name": name}


def province(province_id):
    return {"id": province_id, "name": province_id}


def default_phase():
    return {
        "name": "Spring 1901, Movement",
        "type": "Movement",
        "units": [
            {"type": "Army", "nation": nation("England"), "province": province("lon"), "dislodged": False},
            {"type": "Fleet", "nation": nation("England"), "province": province("nth"), "dislodged": False},
            {"type": "Army", "nation": nation("France"), "province": province("par"), "dislodged": False},
        ],
        "supply_centers": [
            {"province": province("lon"), "nation": nation("England")},
            {"province": province("edi"), "nation": nation("England")},
            {"province": province("par"), "nation": nation("France")},
        ],
    }


class ContextBuilder:
    def __init__(self):
        self._nation = "England"
        self._orders = []
        self._phase = None
        self._channels = []
        self._max_orders = None

    def nation(self, name):
        self._nation = name
        return self

    def phase(self, phase):
        self._phase = phase
        return self

    def order(self, source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
        self._orders.append(option(source, order_type, target, aux, unit_type, named_coast))
        return self

    def orders(self, options):
        self._orders.extend(options)
        return self

    def max_orders(self, value):
        self._max_orders = value
        return self

    def channel(self, *, id, name, private=True, messages):
        self._channels.append(
            {"id": id, "name": name, "private": private, "messages": messages}
        )
        return self

    def build(self) -> ContextData:
        return {
            "orders": self._orders,
            "phase_states": [
                {"max_orders": self._max_orders, "member": {"nation": self._nation}}
            ],
            "game": {"phase_confirmed": False},
            "phase": self._phase if self._phase is not None else default_phase(),
            "channels": self._channels,
            "variant": {},
        }
