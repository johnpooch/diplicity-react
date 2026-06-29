from common.constants import OrderType


class OrderOption:
    def __init__(self, data):
        self._data = data

    @property
    def source_id(self):
        return self._data["source"]["id"]

    @property
    def label(self):
        parts = [self._data["source"]["id"], self._data["order_type"]["id"]]
        for key in ("aux", "target", "unit_type", "named_coast"):
            value = self._data.get(key)
            if value:
                parts.append(value["id"])
        return " ".join(parts)

    def to_selected(self):
        order_type = self._data["order_type"]["id"]
        selected = [self._data["source"]["id"], order_type]

        if order_type == OrderType.BUILD:
            selected.append(self._data["unit_type"]["id"])
            if self._data["named_coast"]:
                selected.append(self._data["named_coast"]["id"])
        elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
            selected.append(self._data["target"]["id"])
            if self._data["named_coast"]:
                selected.append(self._data["named_coast"]["id"])
        elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
            selected.append(self._data["aux"]["id"])
            selected.append(self._data["target"]["id"])

        return selected


class OrderOptionCollection:
    def __init__(self, options):
        self.options = options

    @classmethod
    def from_api(cls, data):
        return cls([OrderOption(option) for option in data])

    def grouped_by_source(self):
        grouped = {}
        for option in self.options:
            grouped.setdefault(option.source_id, []).append(option)
        return grouped

    def first_legal_selections(self):
        first_by_source = {}
        for option in self.options:
            if option.source_id not in first_by_source:
                first_by_source[option.source_id] = option.to_selected()
        return list(first_by_source.values())


class ChatMessage:
    def __init__(self, data):
        self._data = data

    @classmethod
    def list_from_api(cls, data):
        return [cls(message) for message in data]

    @property
    def speaker(self):
        sender = self._data["sender"]
        return "You" if sender["is_current_user"] else sender["name"]

    @property
    def body(self):
        return self._data["body"]
