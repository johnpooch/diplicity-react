from prompt_builder.board import Board, plural
from select_orders.prompt import user_sections
from select_orders.types import Context

RINGS = 3


def _note(board: Board, province: dict) -> str:
    parts = [
        province["type"],
        board.supply_centre_note(province["id"]),
        board.occupancy(province["id"]),
    ]
    return "; ".join(part for part in parts if part)


def build(context: Context) -> str:
    board = Board(context)
    sections = user_sections(context)
    distances = board.distances(board.own_units(), RINGS)
    lines = [
        "Provinces by distance from your nearest unit (armies count a convoy as one move):"
    ]
    for ring in range(1, RINGS + 1):
        provinces = [
            province
            for province in context["provinces"]
            if province["parent_id"] is None and distances.get(province["id"]) == ring
        ]
        if not provinces:
            continue
        lines.append(f"  {plural(ring, 'move')}:")
        lines.extend(
            f"    {province['name']} ({province['id']}) [{_note(board, province)}]"
            for province in provinces
        )
    return "\n\n".join(
        [
            sections["intro"],
            board.powers_summary(),
            "\n".join(lines),
            sections["units"],
            sections["supply_centres"],
            sections["options"],
        ]
    )
