from typing import Protocol

from harness.types import ContextData, TaskContext


class Block(Protocol):
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None: ...
