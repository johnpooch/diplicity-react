import random

from django.conf import settings

from dumbbot.policy import select_orders as dumbbot_select_orders
from harness.adapter import data_to_context
from harness.tasks import reply, select_orders
from inference.constants import InferenceProvider
from inference.models import Inference


def run_dumbbot_orders(*, data):
    context = data_to_context(data)
    return dumbbot_select_orders(context, rng=random.Random())


def run_select_orders(*, data, phase, member):
    context = data_to_context(data)
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task="select_orders",
        system=select_orders.system_prompt(context),
        user_content=select_orders.user_prompt(context),
        output_schema=select_orders.OUTPUT_SCHEMA,
        phase=phase,
        member=member,
    )
    return select_orders.parse_completion(inference.response, context)


def run_reply(*, data, channel_id, phase, member, channel):
    context = data_to_context(data)
    inference = Inference.objects.run(
        provider=InferenceProvider.ANTHROPIC,
        model=settings.BOT_LLM_MODEL,
        task="reply",
        system=reply.system_prompt(),
        user_content=reply.user_prompt(context, channel_id),
        output_schema=reply.OUTPUT_SCHEMA,
        phase=phase,
        member=member,
        channel=channel,
    )
    return reply.parse_completion(inference.response)
