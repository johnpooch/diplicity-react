from harness.evals.runners import DeterministicEval
from harness.evals.select_orders import base_context
from harness.orders import group_options_by_source, option_to_selected
from harness.tasks import SelectOrdersTask


def check(selections, context):
    legal_by_source = {
        source_id: [option_to_selected(option) for option in options]
        for source_id, options in group_options_by_source(context["orders"]).items()
    }
    for selection in selections:
        if selection not in legal_by_source.get(selection[0], []):
            return False, f"illegal selection {selection}"
    return True, f"{len(selections)} legal selection(s)"


EVAL = DeterministicEval(
    name="select_orders.legality",
    task=SelectOrdersTask,
    context=base_context,
    check=check,
)
