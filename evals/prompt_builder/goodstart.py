from collections import deque

from prompt_builder.board import Board
from select_orders.options import option_id
from select_orders.prompt import user_sections
from select_orders.types import Context, OrderOption, Unit

TERRAIN = {"sea": "WATER", "coastal": "COAST", "land": "LAND"}
NEAREST = 3


def _code(province_id: str) -> str:
    return province_id.upper()


def _unit(unit: Unit) -> str:
    return f"{unit['type'][0]} {_code(unit['province'])}"


def _terrain(board: Board, province_id: str) -> str:
    return TERRAIN.get(board.provinces[board.parent(province_id)]["type"], "LAND")


def _paths(board: Board, unit: Unit) -> dict[str, list[str]]:
    start = unit["province"]
    paths = {board.parent(start): [start]}
    seen = {start}
    queue = deque([[start]])
    while queue:
        path = queue.popleft()
        for neighbour in board.neighbours(path[-1], unit["type"]):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append([*path, neighbour])
                paths.setdefault(board.parent(neighbour), [*path, neighbour])
    return paths


def _path(board: Board, path: list[str]) -> str:
    codes: list[str] = []
    for node in path:
        if not codes or codes[-1] != _code(board.parent(node)):
            codes.append(_code(board.parent(node)))
    return f"[{'→'.join(codes)}]"


def _target(option: OrderOption) -> str:
    return _code(option["named_coast"] or option["target"])


def _own_supports(board: Board, unit: Unit, target: str) -> list[OrderOption]:
    source = board.parent(unit["province"])
    return [
        option
        for supporter in board.own_units()
        for option in board.unit_options(supporter)
        if option["order_type"] == "Support"
        and option["aux"] == source
        and option["target"] == target
    ]


def _support_text(board: Board, option: OrderOption) -> str:
    supporter = _unit(board.unit_for(option["source"]))
    supported = _unit(board.unit_for(option["aux"]))
    if option["target"] == option["aux"]:
        return f"{supporter} S {supported}"
    return f"{supporter} S {supported} - {_code(option['target'])}"


def _other_text(board: Board, unit: Unit, option: OrderOption) -> str:
    if option["order_type"] == "Support":
        return _support_text(board, option)
    if option["order_type"] == "Convoy":
        return f"{_unit(unit)} C {_unit(board.unit_for(option['aux']))} - {_code(option['target'])}"
    return f"{_unit(unit)} - {_target(option)} VIA"


def _owner_text(board: Board, province_id: str) -> str:
    owner = board.owners.get(province_id)
    if owner is None:
        return "None"
    return f"{owner.upper()} (You)" if owner == board.nation else owner.upper()


def _occupied(board: Board, province_id: str) -> str:
    occupant = board.unit_for(province_id)
    if occupant is None:
        return "unoccupied"
    if board.mine(occupant):
        return f"occupied by {occupant['nation'].upper()} — you!"
    return f"occupied by {occupant['nation'].upper()}"


def _orders(board: Board, unit: Unit) -> list[tuple[OrderOption, list[OrderOption]]]:
    source = board.parent(unit["province"])
    options = board.unit_options(unit)
    moves = [
        (option, _own_supports(board, unit, option["target"]))
        for option in options
        if option["order_type"] == "Move"
    ]
    holds = [
        (option, _own_supports(board, unit, source))
        for option in options
        if option["order_type"] == "Hold"
    ]
    return [*moves, *holds]


def _order_text(board: Board, unit: Unit, option: OrderOption) -> str:
    if option["order_type"] == "Hold":
        return f"{_unit(unit)} H"
    return f"{_unit(unit)} - {_target(option)}"


def _territory(board: Board, unit: Unit) -> list[str]:
    me = _unit(unit)
    source = board.parent(unit["province"])
    lines = [
        f"<Territory {_code(unit['province'])}>",
        f"  ({_terrain(board, source)})",
        f"  Held by {_owner_text(board, source)}",
        f"  Units present: {me} ({unit['nation'].upper()})",
        "# Adjacent territories:",
    ]
    for province_id in sorted(board.reach(unit["province"], unit["type"])):
        line = f"  {_code(province_id)} ({_terrain(board, province_id)})"
        if board.owners.get(province_id):
            line += f" SC Control: {board.owners[province_id].upper()}"
        occupant = board.unit_for(province_id)
        if occupant:
            line += f" Units: {_unit(occupant)} ({occupant['nation'].upper()})"
        lines.append(line)
        if occupant and board.mine(occupant):
            lines.append(f"    Support hold: {me} S {_unit(occupant)}")
        elif occupant:
            contact = f"{_unit(occupant)} ({occupant['nation'].upper()})"
            lines.append(
                f"    -> {contact} can support or contest {me}’s moves and vice-versa"
            )

    paths = _paths(board, unit)
    lines.append("# Nearest units (not ours):")
    reachable = [
        other
        for other in board.foreign_units()
        if board.parent(other["province"]) in paths
    ]
    reachable.sort(key=lambda other: len(paths[board.parent(other["province"])]))
    for other in reachable[:NEAREST]:
        lines.append(
            f"  {_unit(other)} ({other['nation'].upper()}), path {_path(board, paths[board.parent(other['province'])])}"
        )

    lines.append("# Nearest supply centers (not controlled by us):")
    centres = sorted(
        (len(paths[province_id]), province_id)
        for province_id, owner in board.owners.items()
        if owner != board.nation and province_id in paths
    )
    for _, province_id in centres[:NEAREST]:
        here = " (YOU ARE HERE, hold to capture!)" if province_id == source else ""
        lines.append(
            f"  {_code(province_id)} (Controlled by {_owner_text(board, province_id)}), "
            f"path {_path(board, paths[province_id])}{here}"
        )

    lines.append(f"# Possible {me} unit movements & supports:")
    for option, supports in _orders(board, unit):
        occupied = (
            ""
            if option["order_type"] == "Hold"
            else f" ({_occupied(board, option['target'])})"
        )
        lines.append(
            f"  {option_id(option)}  {_order_text(board, unit, option)}{occupied}"
        )
        lines.extend(
            f"    Available Support: {option_id(support)}  {_support_text(board, support)}"
            for support in supports
        )
    lines.append(f"</Territory {_code(unit['province'])}>")
    return lines


def _summary(board: Board) -> list[str]:
    lines = [
        "# Summary of possible orders (not including supports of other powers' units):"
    ]
    for unit in board.own_units():
        lines.append(f"## {_unit(unit)} possible orders:")
        for option, supports in _orders(board, unit):
            lines.append(f"{option_id(option)}  {_order_text(board, unit, option)}")
            lines.extend(
                f"    {option_id(support)}  {_support_text(board, support)}"
                for support in supports
            )
    return lines


def _others(board: Board) -> list[str] | None:
    shown = {
        option_id(option)
        for unit in board.own_units()
        for order, supports in _orders(board, unit)
        for option in (order, *supports)
    }
    lines = ["Other legal orders (convoys and supports for other powers' units):"]
    for unit in board.own_units():
        rest = [
            option
            for option in board.unit_options(unit)
            if option_id(option) not in shown
        ]
        if rest:
            lines.append(f"## {_unit(unit)}:")
            lines.extend(
                f"  {option_id(option)}  {_other_text(board, unit, option)}"
                for option in rest
            )
    return lines if len(lines) > 1 else None


def _game_map(board: Board) -> list[str]:
    nations = sorted(member["nation"] for member in board.context["members"])
    lines = ["GAME MAP", "Unit Locations:"]
    for nation in nations:
        units = sorted(
            (unit for unit in board.units if unit["nation"] == nation),
            key=lambda unit: unit["province"],
        )
        if units:
            lines.append(
                f"  {nation.upper()}: {len(units)} units – {', '.join(_unit(unit) for unit in units)}"
            )
    lines.extend(["", "Supply Centers:"])
    for nation in nations:
        centres = sorted(
            province_id
            for province_id, owner in board.owners.items()
            if owner == nation
        )
        if centres:
            codes = ", ".join(_code(centre) for centre in centres)
            lines.append(f"  {nation.upper()}: {len(centres)} supply centers – {codes}")
    return lines


def build(context: Context) -> str:
    board = Board(context)
    phase = context["phase"]
    sections = [
        user_sections(context)["intro"],
        "\n".join(_game_map(board)),
        f"POSSIBLE ORDERS FOR {phase['season'].upper()} {phase['year']} {phase['type'].upper()}",
        *("\n".join(_territory(board, unit)) for unit in board.own_units()),
        "\n".join(_summary(board)),
        *(["\n".join(others)] if (others := _others(board)) else []),
        "END POSSIBLE ORDERS",
        "The id at the start of each order line is its option_id.",
    ]
    return "\n\n".join(sections)
