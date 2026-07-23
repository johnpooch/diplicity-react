from harness.evals.runners import DeterministicEval
from harness.evals.select_orders import base_context
from harness.orders import group_options_by_source
from harness.tasks import SelectOrdersTask


def check(selections, context):
    expected = set(group_options_by_source(context["orders"]))
    covered = {selection[0] for selection in selections}
    missing = expected - covered
    if missing:
        return False, f"provinces with no order: {sorted(missing)}"
    return True, f"all {len(expected)} province(s) covered"


EVAL = DeterministicEval(
    name="select_orders.coverage",
    task=SelectOrdersTask,
    context=base_context,
    check=check,
)
