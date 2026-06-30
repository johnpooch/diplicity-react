import logging

from bot.actions.base import Action

logger = logging.getLogger(__name__)

TOOL_NAME = "submit_order_choices"

TOOL = {
    "name": TOOL_NAME,
    "description": "Submit the chosen order index for each unit.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "choices": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_id": {"type": "string"},
                        "option_index": {"type": "integer"},
                    },
                    "required": ["source_id", "option_index"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["choices"],
        "additionalProperties": False,
    },
}

SYSTEM = (
    "You are playing a game of Diplomacy. For each unit listed in the user message, "
    "choose one order by its index from the listed legal options. Submit a choice for "
    "every unit using the submit_order_choices tool."
)


class SelectOrderAction(Action):
    name = "select_order"
    tool = TOOL
    system = SYSTEM

    def __init__(self, options):
        self.options = options

    def build_messages(self):
        lines = []
        for source_id, source_options in self.options.grouped_by_source().items():
            lines.append(f"Unit {source_id}:")
            for index, option in enumerate(source_options):
                lines.append(f"  {index}. {option.label}")
        return [{"role": "user", "content": "\n".join(lines)}]

    def parse(self, tool_input):
        choices = {
            choice["source_id"]: choice["option_index"] for choice in tool_input["choices"]
        }
        selections = []
        for source_id, source_options in self.options.grouped_by_source().items():
            index = choices.get(source_id)
            if index is None or not (0 <= index < len(source_options)):
                chosen = source_options[0]
                logger.info(
                    f"[bot.llm] {source_id}: invalid/missing choice {index}; "
                    f"using first legal option {chosen.label}"
                )
            else:
                chosen = source_options[index]
                logger.info(f"[bot.llm] {source_id}: chose {chosen.label}")
            selections.append(chosen.to_selected())
        logger.info(f"[bot.llm] selected {len(selections)} order(s)")
        return selections
