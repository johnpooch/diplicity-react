from prompt_builder.board import Board, join_and, listed
from select_orders.options import describe_option, group_options_by_source, option_id
from select_orders.prompt import user_sections
from select_orders.types import Context, OrderOption, Unit


def _whose(board: Board, unit: Unit) -> str:
    return "your unit" if board.mine(unit) else f"a {board.adjective(unit['nation'])} unit"


def _fleets(board: Board, route: list[str]) -> str:
    return join_and([board.fleet_name(fleet) for fleet in board.route_fleets(route)])


def _crossing(board: Board, unit: Unit, option: OrderOption) -> str | None:
    target = option["target"]
    if option["order_type"] == "Move" and (unit["type"] != "Army" or board.can_move(unit, target)):
        return None
    army = board.parent(unit["province"])
    route = board.convoy_route(army, target)
    if route is None:
        return "crosses water: no fleets can convoy it"
    convoy = f"Convoy {board.name(army)} -> {board.name(target)}"
    return f"crosses water: fails unless {_fleets(board, route)} orders {convoy}"


def _move_note(board: Board, unit: Unit, option: OrderOption) -> str:
    note = board.move_note(option["target"])
    crossing = _crossing(board, unit, option)
    return f"{note}; {crossing}" if crossing else note


def _support_note(board: Board, option: OrderOption) -> str:
    supported = board.unit_for(option["aux"])
    if supported is None:
        return "no unit to support"
    target = option["target"]
    if target == option["aux"]:
        attackers = listed([board.owned_short(unit) for unit in board.movers(target, [supported])])
        return f"supports {_whose(board, supported)} to hold; foreign units that can attack it: {attackers}"
    rivals = listed([board.owned_short(unit) for unit in board.movers(target, [supported])])
    note = (
        f"supports {_whose(board, supported)}; only useful if that unit orders this move; "
        f"foreign units that can also move to {board.name(target)}: {rivals}"
    )
    occupant = board.unit_for(target)
    return f"{note}; occupied by {board.owned_short(occupant)}" if occupant else note


def _convoy_note(board: Board, unit: Unit, option: OrderOption) -> str:
    army = board.unit_for(option["aux"])
    fleet = board.parent(unit["province"])
    target = option["target"]
    carried = f"your {board.unit_name(army)}" if board.mine(army) else f"{army['nation']} {board.unit_name(army)}"
    alternative = board.convoy_route(option["aux"], target, avoid=fleet)
    if alternative is not None:
        return f"convoys {carried}; not needed: {_fleets(board, alternative)} can carry this convoy without this fleet"
    route = board.convoy_route_through(option["aux"], target, fleet) or [fleet]
    others = [sea for sea in route if sea != fleet]
    note = f"convoys {carried}; only useful if it orders MoveViaConvoy -> {board.name(target)}"
    return f"{note} and {_fleets(board, others)} also convoys" if others else note


def _note(board: Board, unit: Unit, option: OrderOption) -> str:
    order_type = option["order_type"]
    if order_type == "Hold":
        attackers = listed([board.owned_short(other) for other in board.movers(board.parent(unit["province"]))])
        return f"foreign units that can move here: {attackers}"
    if order_type in ("Move", "MoveViaConvoy"):
        return _move_note(board, unit, option)
    if order_type == "Support":
        return _support_note(board, option)
    if order_type == "Convoy":
        return _convoy_note(board, unit, option)
    return ""


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    lines = ["Your available orders (bracketed notes describe the board around each order):"]
    for source, options in group_options_by_source(context["order_options"]).items():
        unit = board.unit_for(source)
        lines.append(f"  {board.name(source)} ({source}):")
        for option in options:
            note = _note(board, unit, option) if unit else ""
            suffix = f" [{note}]" if note else ""
            lines.append(f"    {option_id(option)} ({describe_option(option, context)}){suffix}")
    if len(lines) == 1:
        lines.append("  (none)")
    return "\n\n".join([*(text for name, text in sections.items() if name != "options"), "\n".join(lines)])
