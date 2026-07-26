from django.conf import settings

from harness.prompt import build_prompt
from inference.constants import InferenceProvider
from inference.models import Inference


def run_task(task, *, context, task_ctx, phase, member, channel=None):
    prompt = build_prompt(task, context, task_ctx)
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task=task.name,
        system=prompt.system,
        user_content=prompt.user_content,
        output_schema=prompt.output_schema,
        max_tokens=prompt.max_tokens,
        phase=phase,
        member=member,
        channel=channel,
    )
    return task.parse(inference.response, context=context)
