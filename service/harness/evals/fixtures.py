from harness.types import ContextData


def _field(value):
    return {"id": value, "label": value} if value is not None else None


def _option(source, order_type, target=None, aux=None, unit_type=None, named_coast=None):
    return {
        "source": _field(source),
        "order_type": _field(order_type),
        "target": _field(target),
        "aux": _field(aux),
        "unit_type": _field(unit_type),
        "named_coast": _field(named_coast),
    }


def _nation(name):
    return {"nation_id": name.lower(), "name": name}


def _province(province_id):
    return {"id": province_id, "name": province_id}


def _phase():
    return {
        "name": "Spring 1901, Movement",
        "type": "Movement",
        "units": [
            {"type": "Army", "nation": _nation("England"), "province": _province("lon"), "dislodged": False},
            {"type": "Fleet", "nation": _nation("England"), "province": _province("nth"), "dislodged": False},
            {"type": "Army", "nation": _nation("France"), "province": _province("par"), "dislodged": False},
        ],
        "supply_centers": [
            {"province": _province("lon"), "nation": _nation("England")},
            {"province": _province("edi"), "nation": _nation("England")},
            {"province": _province("par"), "nation": _nation("France")},
        ],
    }


def select_orders_context() -> ContextData:
    return {
        "orders": [
            _option("lon", "Hold"),
            _option("lon", "Move", target="wal"),
            _option("nth", "Hold"),
            _option("nth", "Move", target="edi"),
        ],
        "phase_states": [{"max_orders": None, "member": {"nation": "England"}}],
        "game": {"phase_confirmed": False},
        "phase": _phase(),
        "channels": [],
        "variant": {},
    }


def reply_context() -> ContextData:
    return {
        "orders": [],
        "phase_states": [{"member": {"nation": "England"}}],
        "game": {"phase_confirmed": False},
        "phase": _phase(),
        "channels": [
            {
                "id": 1,
                "name": "England, France",
                "private": True,
                "messages": [
                    {
                        "id": 1,
                        "body": "Shall we agree the Channel stays empty this year?",
                        "sender": {"is_current_user": False, "nation": _nation("France")},
                    }
                ],
            }
        ],
        "variant": {},
    }
