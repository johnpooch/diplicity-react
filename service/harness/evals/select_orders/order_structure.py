from harness.evals.runners import DeterministicEval
from harness.evals.select_orders import base_context
from harness.tasks import SelectOrdersTask


def check(selections, context):
    if not isinstance(selections, list):
        return False, "result is not a list"
    if not all(isinstance(s, list) and len(s) >= 2 for s in selections):
        return False, "malformed selection"
    return True, f"{len(selections)} well-formed selection(s)"


EVAL = DeterministicEval(
    name="select_orders.structure",
    task=SelectOrdersTask,
    context=base_context,
    check=check,
)
