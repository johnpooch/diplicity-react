from django.conf import settings

from harness.prompt import build_prompt
from harness_v2.adapter import data_to_context
from harness_v2.persona import render_persona
from harness_v2.tasks.select_orders.parser import parse_completion
from harness_v2.tasks.select_orders.schema import OUTPUT_SCHEMA
from harness_v2.tasks.select_orders.system_prompt import system_prompt
from harness_v2.tasks.select_orders.user_prompt import user_prompt
from inference.constants import InferenceProvider
from inference.models import Inference


def run_select_orders(*, data, persona, phase, member):
    context = data_to_context(data)
    system = system_prompt(context)
    if persona:
        system = f"{system}\n\n{render_persona(persona)}"
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task="select_orders",
        system=system,
        user_content=user_prompt(context),
        output_schema=OUTPUT_SCHEMA,
        phase=phase,
        member=member,
    )
    return parse_completion(inference.response, context)


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
