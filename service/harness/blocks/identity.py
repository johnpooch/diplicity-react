from harness.types import ContextData, TaskContext


class IdentityBlock:
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None:
        phase_states = context["phase_states"]
        nation = phase_states[0].get("member", {}).get("nation") if phase_states else None
        if not nation:
            return None
        return f"You are playing {nation}."
