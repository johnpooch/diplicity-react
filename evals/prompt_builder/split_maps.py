from prompt_builder.board import Board, join_and
from select_orders.prompt import user_sections
from select_orders.types import Context


def _map(board: Board, header: str, allows: str) -> str:
    lines = [header]
    for province in board.context["provinces"]:
        targets = [
            adjacency["to"]
            for adjacency in province["adjacencies"]
            if allows in adjacency["allows"]
        ]
        if not targets:
            continue
        centre = " [supply centre]" if province["supply_center"] else ""
        lines.append(
            f"  {province['name']} ({province['id']}){centre} -> {', '.join(board.name(t) for t in targets)}"
        )
    return "\n".join(lines)


def _convoys(board: Board) -> str | None:
    lines = [
        "Convoy routes for your armies this phase "
        "(an army can only cross water if every fleet named orders the matching Convoy):"
    ]
    for unit in board.own_units():
        if unit["type"] != "Army":
            continue
        army = board.parent(unit["province"])
        for target in board.convoy_targets(unit):
            route = board.convoy_route(army, target)
            if route is None:
                continue
            fleets = join_and(
                [board.fleet_name(fleet) for fleet in board.route_fleets(route)]
            )
            lines.append(
                f"  {board.unit_name(unit)} -> {board.name(target)}: needs {fleets} to order "
                f"Convoy {board.name(army)} -> {board.name(target)}"
            )
    return "\n".join(lines) if len(lines) > 1 else None


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    maps = [
        _map(board, "Fleet map (where a fleet in each province can move):", "fleet"),
        _map(
            board, "Army map (where an army in each province can move by land):", "army"
        ),
        _convoys(board),
    ]
    ordered = []
    for name, text in sections.items():
        if name == "board":
            ordered.extend(section for section in maps if section is not None)
        else:
            ordered.append(text)
    return "\n\n".join(ordered)
