import logging

from harness.blocks._format import format_channel
from harness.types import ContextData, TaskContext

logger = logging.getLogger(__name__)


class ChannelMessagesBlock:
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None:
        channel = next(
            (c for c in context["channels"] if c["id"] == task_ctx.channel_id), None
        )
        if channel is None:
            logger.info(
                f"[harness.blocks] channel {task_ctx.channel_id} not in fetched data; skipping"
            )
            return None
        return format_channel(channel)
