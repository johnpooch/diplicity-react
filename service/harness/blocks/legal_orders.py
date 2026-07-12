from harness.orders import group_options_by_source, order_option_label
from harness.types import ContextData, TaskContext


class LegalOrdersBlock:
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None:
        lines = ["Legal orders:"]
        options_by_source = group_options_by_source(context["orders"])
        for source_id in sorted(options_by_source):
            lines.append(f"Unit {source_id}:")
            for index, option in enumerate(options_by_source[source_id]):
                lines.append(f"  {index}. {order_option_label(option)}")
        return "\n".join(lines)
