from collections.abc import Callable

from prompt_builder import (
    annotated_options,
    contest_table,
    distance_rings,
    goodstart,
    local_board,
    own_units_first,
    split_maps,
)
from select_orders.types import Context

VARIANTS: dict[str, Callable[[Context], str]] = {
    "user_1_own_units_first": own_units_first.build,
    "user_2_contest_table": contest_table.build,
    "user_3_split_fleet_army_maps": split_maps.build,
    "user_4_annotated_options": annotated_options.build,
    "user_5_distance_rings": distance_rings.build,
    "user_6_local_board_only": local_board.build,
    "user_7_goodstart_style": goodstart.build,
}
