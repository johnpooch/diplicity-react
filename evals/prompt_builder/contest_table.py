from prompt_builder.board import Board, join_and, listed
from select_orders.prompt import user_sections
from select_orders.types import Context


def _owner(board: Board, owner: str | None) -> str:
    if owner is None:
        return "unowned"
    return "yours" if owner == board.nation else owner


def _reachers(board: Board, province_id: str) -> list[str]:
    reachers = []
    for unit in board.own_units():
        if board.can_move(unit, province_id):
            reachers.append(board.short(unit))
            continue
        route = (
            board.convoy_route(board.parent(unit["province"]), province_id)
            if province_id in board.convoy_targets(unit)
            else None
        )
        if route is not None:
            via = join_and([board.name(sea) for sea in route])
            reachers.append(f"{board.short(unit)} (convoy via {via})")
    return reachers


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    lines = [
        "Supply centres in reach (who can move into each one this phase; "
        "armies by convoy only if the fleets convoy them):"
    ]
    for center in context["supply_centers"]:
        province_id = center["province"]
        reachers = _reachers(board, province_id)
        if not reachers:
            continue
        others = listed([board.owned_short(unit) for unit in board.movers(province_id)])
        lines.append(
            f"  {board.name(province_id)} ({province_id}): {_owner(board, center['nation'])}, "
            f"{board.occupancy(province_id)} | your units: {', '.join(reachers)} | other powers: {others}"
        )
    if len(lines) == 1:
        lines.append("  (none)")
    before = [text for name, text in sections.items() if name != "options"]
    return "\n\n".join([*before, "\n".join(lines), sections["options"]])
