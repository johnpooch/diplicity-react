from prompt_builder.board import Board, board_lines
from select_orders.prompt import user_sections
from select_orders.types import Context

NEAR = 2


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    near_units = board.near_foreign_units(NEAR)
    rest = [
        unit
        for unit in board.foreign_units()
        if not any(unit is near for near in near_units)
    ]

    local = [
        "Board near your units (provinces within two moves) (adjacency: A=army only, F=fleet only, AF=both):",
        *board_lines(context, set(board.near_province_ids(NEAR))),
    ]
    units = [
        "Units on the board (yours, then foreign units near yours, then the rest):",
        *(board.unit_line(unit) for unit in [*board.own_units(), *near_units, *rest]),
    ]

    replaced = {"board": "\n".join(local), "units": "\n".join(units)}
    return "\n\n".join(replaced.get(name, text) for name, text in sections.items())
