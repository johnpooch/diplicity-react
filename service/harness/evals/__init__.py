import importlib
import pkgutil

TASK_PACKAGES = {
    "select_orders": "harness.evals.select_orders",
    "reply": "harness.evals.reply",
}


def discover(task_name=None):
    evals = []
    names = [task_name] if task_name else list(TASK_PACKAGES)
    for name in names:
        package = importlib.import_module(TASK_PACKAGES[name])
        for module_info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{TASK_PACKAGES[name]}.{module_info.name}")
            eval_spec = getattr(module, "EVAL", None)
            if eval_spec is not None:
                evals.append(eval_spec)
    return evals
