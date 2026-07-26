from harness.blocks import render_persona
from harness.tasks.base import TaskDefinition
from harness.types import ContextData, Prompt, TaskContext


def build_prompt(
    task: type[TaskDefinition], context: ContextData, task_ctx: TaskContext
) -> Prompt:
    body = "\n\n".join(
        rendered
        for block in task.blocks
        for rendered in [block.render(context, task_ctx)]
        if rendered
    )
    system = task.system_prompt
    if task_ctx.persona:
        system = f"{system}\n\n{render_persona(task_ctx.persona)}"
    user_content = "\n\n".join(part for part in [body, task.instruction] if part)
    return Prompt(
        system=system,
        user_content=user_content,
        output_schema=task.output_schema,
        max_tokens=task.max_tokens,
    )
