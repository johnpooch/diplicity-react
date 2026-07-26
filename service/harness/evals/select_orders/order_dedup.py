from harness.evals.runners import DeterministicEval
from harness.evals.select_orders import base_context
from harness.tasks import SelectOrdersTask


def check(selections, context):
    sources = [selection[0] for selection in selections]
    duplicates = {source for source in sources if sources.count(source) > 1}
    if duplicates:
        return False, f"provinces ordered more than once: {sorted(duplicates)}"
    return True, f"{len(sources)} province(s), no duplicates"


EVAL = DeterministicEval(
    name="select_orders.dedup",
    task=SelectOrdersTask,
    context=base_context,
    check=check,
)
