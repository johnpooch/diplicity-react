from harness.types import ContextData, TaskContext


class PhaseStateBlock:
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None:
        phase_states = context["phase_states"]
        if not phase_states:
            return None
        max_orders = phase_states[0].get("max_orders")
        if max_orders is None:
            return None
        return f"Orders to submit this phase: {max_orders}"
