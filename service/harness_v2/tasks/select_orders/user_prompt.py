from harness_v2.exceptions import ContextError
from harness_v2.tasks.select_orders.options import describe_option, group_options_by_source
from harness_v2.types import Context

REQUIRED_FIELDS = ("members", "phase", "provinces", "order_options")

ALLOWS_LABEL = {
    ("army",): "A",
    ("fleet",): "F",
    ("army", "fleet"): "AF",
}


def current_nation(context: Context) -> str:
    for member in context["members"]:
        if member["is_current_user"]:
            return member["nation"]
    raise ContextError("context has no current-user member")


def user_prompt(context: Context) -> str:
    for field in REQUIRED_FIELDS:
        if field not in context:
            raise ContextError(f"context is missing required field '{field}'")

    nation = current_nation(context)
    names = {province["id"]: province["name"] for province in context["provinces"]}
    phase = context["phase"]

    lines = [
        f"You are playing as {nation}.",
        f"The current phase is {phase['season']} {phase['year']}, {phase['type']}.",
    ]

    max_orders = context.get("max_orders")
    if max_orders is not None:
        lines.append(f"You may submit at most {max_orders} order(s) this phase.")

    if len(context["members"]) > 1:
        lines.append("")
        lines.append("Players:")
        for member in context["members"]:
            marker = " [you]" if member["is_current_user"] else ""
            lines.append(f"  {member['nation']}{marker}")

    if context["provinces"]:
        lines.append("")
        lines.append("Board (adjacency: A=army only, F=fleet only, AF=both):")
        for province in context["provinces"]:
            supply_center = " [supply centre]" if province["supply_center"] else ""
            adjacencies = ", ".join(
                f"{names.get(adjacency['to'], adjacency['to'])}({ALLOWS_LABEL[tuple(adjacency['allows'])]})"
                for adjacency in province["adjacencies"]
            )
            lines.append(f"  {province['name']} ({province['id']}, {province['type']}){supply_center} -> {adjacencies}")

    if context["units"]:
        lines.append("")
        lines.append("Units on the board:")
        for unit in context["units"]:
            mine = " [yours]" if unit["nation"] == nation else ""
            dislodged = " [DISLODGED]" if unit["dislodged"] else ""
            province = names.get(unit["province"], unit["province"])
            lines.append(f"  {unit['type']} {province} — {unit['nation']}{mine}{dislodged}")

    if context["supply_centers"]:
        lines.append("")
        lines.append("Supply centres:")
        for center in context["supply_centers"]:
            owner = center["nation"] or "UNCONTROLLED"
            mine = " [yours]" if center["nation"] == nation else ""
            province = names.get(center["province"], center["province"])
            lines.append(f"  {province} — {owner}{mine}")

    lines.append("")
    lines.append("Your available orders:")
    grouped = group_options_by_source(context["order_options"])
    if not grouped:
        lines.append("  (none)")
    for source_id, options in grouped.items():
        lines.append(f"  {names.get(source_id, source_id)} ({source_id}):")
        for index, option in enumerate(options):
            lines.append(f"    {index}. {describe_option(option, context)}")

    return "\n".join(lines)
