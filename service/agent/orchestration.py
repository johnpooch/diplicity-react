from django.conf import settings

from harness.adapter import data_to_context
from harness.persona import render_persona
from harness.tasks import reply, select_orders
from inference.constants import InferenceProvider
from inference.models import Inference


def _system(task_system_prompt, persona):
    if persona:
        return f"{task_system_prompt}\n\n{render_persona(persona)}"
    return task_system_prompt


def run_select_orders(*, data, persona, phase, member):
    context = data_to_context(data)
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task="select_orders",
        system=_system(select_orders.system_prompt(context), persona),
        user_content=select_orders.user_prompt(context),
        output_schema=select_orders.OUTPUT_SCHEMA,
        phase=phase,
        member=member,
    )
    return select_orders.parse_completion(inference.response, context)


def run_reply(*, data, channel_id, persona, phase, member, channel):
    context = data_to_context(data)
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task="reply",
        system=_system(reply.system_prompt(), persona),
        user_content=reply.user_prompt(context, channel_id),
        output_schema=reply.OUTPUT_SCHEMA,
        phase=phase,
        member=member,
        channel=channel,
    )
    return reply.parse_completion(inference.response)
