import logging

from harness.blocks import GameStateBlock, IdentityBlock, LegalOrdersBlock, PhaseStateBlock
from harness.exceptions import ParseError
from harness.orders import group_options_by_source, option_to_selected, order_option_label
from harness.prompts import load_prompt
from harness.tasks.base import TaskDefinition, extract_json
from harness.types import ContextData

logger = logging.getLogger(__name__)

ORDER_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
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
        },
    },
    "required": ["reasoning", "choices"],
    "additionalProperties": False,
}


class SelectOrdersTask(TaskDefinition):
    name = "select_orders"
    system_prompt = load_prompt("select_orders_system.txt")
    instruction = load_prompt("select_orders_instruction.txt")
    blocks = (GameStateBlock(), IdentityBlock(), LegalOrdersBlock(), PhaseStateBlock())
    output_schema = ORDER_SELECTION_SCHEMA

    @classmethod
    def parse(cls, response: str, *, context: ContextData) -> list[list[str]]:
        data = extract_json(response)

        reasoning = data.get("reasoning")
        if reasoning:
            logger.info(f"[harness.select_orders] reasoning: {reasoning}")

        if not isinstance(data.get("choices"), list):
            raise ParseError("response has no choices")

        choices = {}
        for choice in data["choices"]:
            if isinstance(choice, dict) and "source_id" in choice and "option_index" in choice:
                choices[choice["source_id"]] = choice["option_index"]

        selections = []
        for source_id, source_options in group_options_by_source(context["orders"]).items():
            index = choices.get(source_id)
            if not isinstance(index, int) or not (0 <= index < len(source_options)):
                logger.info(
                    f"[harness.select_orders] {source_id}: invalid/missing choice {index}; skipping"
                )
                continue
            chosen = source_options[index]
            logger.info(f"[harness.select_orders] {source_id}: chose {order_option_label(chosen)}")
            selections.append(option_to_selected(chosen))

        if context["orders"] and not selections:
            raise ParseError("no valid selection produced")
        logger.info(f"[harness.select_orders] selected {len(selections)} order(s)")
        return selections
