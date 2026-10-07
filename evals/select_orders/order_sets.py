from select_orders.types import Fixture, OrderSetLabel


def order_set_key(option_ids: list[str]) -> list[str]:
    return sorted(set(option_ids))


def order_set_label(fixture: Fixture, option_ids: list[str]) -> OrderSetLabel | None:
    key = order_set_key(option_ids)
    return next((entry for entry in fixture.get("order_set_labels", []) if entry["orders"] == key), None)


def label_order_set(
    fixture: Fixture, option_ids: list[str], label: str, labeller: str, labelled_at: str, reason: str | None = None
) -> Fixture:
    entry: OrderSetLabel = {
        "orders": order_set_key(option_ids),
        "label": label,
        "labeller": labeller,
        "labelled_at": labelled_at,
    }
    if reason:
        entry["reason"] = reason
    existing = fixture.get("order_set_labels", [])
    if order_set_label(fixture, option_ids) is None:
        return {**fixture, "order_set_labels": [*existing, entry]}
    return {**fixture, "order_set_labels": [entry if kept["orders"] == entry["orders"] else kept for kept in existing]}
