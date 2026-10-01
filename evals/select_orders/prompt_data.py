from select_orders.exceptions import ContextError
from select_orders.options import describe_option, group_options_by_source, option_id
from select_orders.types import Context
from select_orders.utils import current_nation

REQUIRED_FIELDS = ("members", "phase", "provinces", "order_options")

ALLOWS_LABEL = {
    ("army",): "A",
    ("fleet",): "F",
    ("army", "fleet"): "AF",
}


def prompt_data(context: Context) -> dict:
    for field in REQUIRED_FIELDS:
        if field not in context:
            raise ContextError(f"context is missing required field '{field}'")

    nation = current_nation(context)
    names = {province["id"]: province["name"] for province in context["provinces"]}
    phase = context["phase"]

    return {
        "intro": {
            "nation": nation,
            "season": phase["season"],
            "year": phase["year"],
            "phase_type": phase["type"],
            "max_orders": context.get("max_orders"),
        },
        "players": (
            [
                {"nation": member["nation"], "is_current_user": member["is_current_user"]}
                for member in context["members"]
            ]
            if len(context["members"]) > 1
            else []
        ),
        "board": [
            {
                "id": province["id"],
                "name": province["name"],
                "type": province["type"],
                "supply_center": province["supply_center"],
                "adjacencies": [
                    {
                        "name": names.get(adjacency["to"], adjacency["to"]),
                        "allows": ALLOWS_LABEL[tuple(adjacency["allows"])],
                    }
                    for adjacency in province["adjacencies"]
                ],
            }
            for province in context["provinces"]
        ],
        "units": [
            {
                "type": unit["type"],
                "province": names.get(unit["province"], unit["province"]),
                "nation": unit["nation"],
                "mine": unit["nation"] == nation,
                "dislodged": unit["dislodged"],
            }
            for unit in context["units"]
        ],
        "supply_centres": [
            {
                "province": names.get(center["province"], center["province"]),
                "owner": center["nation"],
                "mine": center["nation"] == nation,
            }
            for center in context["supply_centers"]
        ],
        "options": [
            {
                "id": source_id,
                "name": names.get(source_id, source_id),
                "options": [
                    {"id": option_id(option), "description": describe_option(option, context)} for option in options
                ],
            }
            for source_id, options in group_options_by_source(context["order_options"]).items()
        ],
    }
