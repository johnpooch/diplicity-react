from prompt_builder.board import Board, board_lines, join_and, listed
from select_orders.prompt import user_sections
from select_orders.types import Context

NEAR = 2


def _unit_lines(board: Board) -> list[str]:
    lines = ["Your units and where each can go this phase:"]
    for unit in board.own_units():
        lines.append(f"  {board.unit_name(unit)} ({unit['province']})")
        destinations = board.reach(unit["province"], unit["type"])
        lines.append("    can move to:" if unit["type"] == "Fleet" else "    by land:")
        lines.extend(
            f"      {board.name(target)} ({target}) [{board.move_note(target)}]"
            for target in destinations
        )
        if not destinations:
            lines.append("      (none)")
        convoys = [
            (target, route)
            for target in board.convoy_targets(unit)
            if (route := board.convoy_route(board.parent(unit["province"]), target))
            is not None
        ]
        if convoys:
            lines.append(
                "    by convoy (only if the named fleets order the matching Convoy):"
            )
            for target, route in convoys:
                fleets = join_and(
                    [board.fleet_name(fleet) for fleet in board.route_fleets(route)]
                )
                lines.append(
                    f"      {board.name(target)} ({target}) via {fleets} [{board.move_note(target)}]"
                )
    return lines


def _threat_lines(board: Board) -> list[str]:
    lines = ["Threats to your supply centres:"]
    for center in board.context["supply_centers"]:
        if center["nation"] != board.nation:
            continue
        province_id = center["province"]
        distances = [
            (unit, board.moves_away(unit, 2).get(province_id))
            for unit in board.foreign_units()
        ]
        now = [board.owned_short(unit) for unit, distance in distances if distance == 1]
        later = [
            board.owned_short(unit) for unit, distance in distances if distance == 2
        ]
        lines.append(
            f"  {board.name(province_id)} ({province_id}): can be entered this phase by: {listed(now)}; "
            f"two moves away: {listed(later)}"
        )
    return lines


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    near_units = board.near_foreign_units(NEAR)
    near_ids = set(board.near_province_ids(NEAR))

    foreign = ["Foreign units within two moves of your units:"]
    foreign.extend(board.unit_line(unit) for unit in near_units)
    if not near_units:
        foreign.append("  (none)")

    local = [
        "Local map, provinces within two moves of your units (adjacency: A=army only, F=fleet only, AF=both):"
    ]
    local.extend(board_lines(context, near_ids))

    others = [
        unit
        for unit in board.foreign_units()
        if not any(unit is near for near in near_units)
    ]
    rest = ["Other units on the board:", *(board.unit_line(unit) for unit in others)]

    return "\n\n".join(
        [
            sections["intro"],
            board.powers_summary(),
            "\n".join(_unit_lines(board)),
            "\n".join(_threat_lines(board)),
            "\n".join(foreign),
            "\n".join(local),
            *(["\n".join(rest)] if others else []),
            sections["options"],
        ]
    )
