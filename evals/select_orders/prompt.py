from functools import lru_cache

from jinja2 import Environment, StrictUndefined, Template, TemplateError

from select_orders.constants import PhaseType
from select_orders.exceptions import PromptError
from select_orders.prompt_data import prompt_data
from select_orders.types import Context

DEFAULT_PARTS = {
    "system.role": """You are an expert Diplomacy player. You will be given the state of a game and \
the complete list of legal orders available to you this phase, grouped by the province \
that issues them.""",
    "system.principles": """Principles for choosing orders:
- Move units closer to supply centres you could capture, even when the square you move to \
has none itself. A move only wastes the turn if it carries a unit away from every centre it \
could contest or into a corner it cannot advance from.
- Holding does nothing for a unit's position. Hold only to defend a province genuinely under \
threat this phase; do not hold merely because no move stands out.
- A support helps only when both hold: the unit you support is actually ordered to make \
exactly that move or hold this phase, and an enemy could otherwise contest that province. If \
the supported action is not being made, or no enemy can reach the province, the support is \
wasted — use the unit elsewhere.
- Choose your orders as a set, not one unit at a time. If two of your own units would move to \
the same province they bounce and both fail, so send one of them elsewhere unless the bounce \
itself serves a purpose.
- Support or act for another power's unit only when it advances your own position and \
follows a coordination you have agreed with them; without such an agreement, a unit spent \
on a rival's move is spent for their benefit.""",
    "system.task.movement": """Select exactly one order for every province listed. A province with no \
order does nothing, which is almost always worse than the weakest listed alternative.""",
    "system.task.retreat": """Each province listed holds a dislodged unit that must be dealt with this \
phase. Select exactly one order for every province listed. A unit given no order is \
destroyed.""",
    "system.task.adjustment": """You may not order every province listed. Select orders for exactly \
{{ max_orders }} of them and leave the rest alone, choosing the {{ max_orders }} that most improve \
your position.""",
    "system.task.adjustment_unknown": """You may not order every province listed. Select orders only for \
the provinces you are entitled to adjust this phase, and leave the rest alone.""",
    "system.format": """Respond with JSON only. No markdown fences, no prose outside the JSON. Use this \
shape:

{"reasoning": "<brief explanation of your plan>", "choices": [{"option_id": "<option id>"}]}

The option_id is the id at the start of each line in your list of available orders. Copy \
it exactly. Give at most one entry per province.""",
    "user.intro": """You are playing as {{ nation }}.
The current phase is {{ season }} {{ year }}, {{ phase_type }}.""",
    "user.max_orders": "You may submit at most {{ max_orders }} order(s) this phase.",
    "user.players.header": "Players:",
    "user.players.line": "  {{ nation }}{{ ' [you]' if is_current_user else '' }}",
    "user.board.header": "Board (adjacency: A=army only, F=fleet only, AF=both):",
    "user.board.line": "  {{ name }} ({{ id }}, {{ type }}){{ ' [supply centre]' if supply_center else '' }} -> {{ adjacencies }}",
    "user.board.adjacency": "{{ name }}({{ allows }})",
    "user.units.header": "Units on the board:",
    "user.units.line": "  {{ type }} {{ province }} — {{ nation }}{{ ' [yours]' if mine else '' }}{{ ' [DISLODGED]' if dislodged else '' }}",
    "user.supply_centres.header": "Supply centres:",
    "user.supply_centres.line": "  {{ province }} — {{ owner or 'UNCONTROLLED' }}{{ ' [yours]' if mine else '' }}",
    "user.options.header": "Your available orders:",
    "user.options.province": "  {{ name }} ({{ id }}):",
    "user.options.line": "    {{ id }} ({{ description }})",
    "user.options.empty": "  (none)",
}

ENVIRONMENT = Environment(undefined=StrictUndefined, keep_trailing_newline=True)


@lru_cache(maxsize=256)
def _template(text: str) -> Template:
    return ENVIRONMENT.from_string(text)


def _render(parts: dict[str, str], part: str, values: dict | None = None) -> str:
    try:
        return _template(parts[part]).render(values or {})
    except TemplateError as e:
        raise PromptError(f"part '{part}' failed to render: {e}") from e


def _parts(overrides: dict[str, str] | None) -> dict[str, str]:
    unknown = sorted(set(overrides or {}) - set(DEFAULT_PARTS))
    if unknown:
        raise PromptError(f"unknown prompt parts: {unknown}")
    return {**DEFAULT_PARTS, **(overrides or {})}


def _task_part(context: Context) -> str:
    phase_type = context["phase"]["type"]
    if phase_type == PhaseType.ADJUSTMENT:
        if context.get("max_orders") is None:
            return "system.task.adjustment_unknown"
        return "system.task.adjustment"
    if phase_type == PhaseType.RETREAT:
        return "system.task.retreat"
    return "system.task.movement"


def _section(parts: dict[str, str], name: str, items: list[dict]) -> str | None:
    if not items:
        return None
    lines = [_render(parts, f"user.{name}.header")]
    lines.extend(_render(parts, f"user.{name}.line", item) for item in items)
    return "\n".join(lines)


def system_prompt(context: Context, overrides: dict[str, str] | None = None) -> str:
    parts = _parts(overrides)
    return "\n\n".join(
        [
            _render(parts, "system.role"),
            _render(parts, "system.principles"),
            _render(parts, _task_part(context), {"max_orders": context.get("max_orders")}),
            _render(parts, "system.format"),
        ]
    )


def user_prompt(context: Context, overrides: dict[str, str] | None = None) -> str:
    parts = _parts(overrides)
    data = prompt_data(context)

    intro = [_render(parts, "user.intro", data["intro"])]
    if data["intro"]["max_orders"] is not None:
        intro.append(_render(parts, "user.max_orders", data["intro"]))

    board = [
        {
            **province,
            "adjacencies": ", ".join(
                _render(parts, "user.board.adjacency", adjacency) for adjacency in province["adjacencies"]
            ),
        }
        for province in data["board"]
    ]

    options = [_render(parts, "user.options.header")]
    if not data["options"]:
        options.append(_render(parts, "user.options.empty"))
    for province in data["options"]:
        options.append(_render(parts, "user.options.province", province))
        options.extend(_render(parts, "user.options.line", option) for option in province["options"])

    sections = [
        "\n".join(intro),
        _section(parts, "players", data["players"]),
        _section(parts, "board", board),
        _section(parts, "units", data["units"]),
        _section(parts, "supply_centres", data["supply_centres"]),
        "\n".join(options),
    ]
    return "\n\n".join(section for section in sections if section is not None)
