import logging

from django.conf import settings
from procrastinate.contrib.django import app

from bot.api_client import ApiClient, ApiClientError
from bot.context import (
    ContextBuilder,
    fetch_context,
    first_legal_selections,
    parse_order_selections,
    parse_reply,
)
from bot.llm_client import LLMClient, LLMError
from bot.prompts import load_prompt

logger = logging.getLogger(__name__)


def _submit_orders_from_context(api, data, game_id, label):
    builder = (
        ContextBuilder(data)
        .with_orders()
        .with_phase_state()
        .with_conversations()
    )
    system = load_prompt("select_orders_system.txt")
    instruction = load_prompt("select_orders_instruction.txt")
    user_content = "\n\n".join(
        part for part in [builder.build_shared(), builder.build_private(), instruction] if part
    )

    try:
        response_text = LLMClient(settings.ANTHROPIC_API_KEY).complete(
            system=system, messages=[{"role": "user", "content": user_content}]
        )
        selections = parse_order_selections(response_text, data["orders"])
    except LLMError as e:
        logger.info(f"[{label}] {e}; using first-legal selection")
        selections = first_legal_selections(data["orders"])

    phase_states = data["phase_states"]
    max_orders = phase_states[0].get("max_orders") if phase_states else None
    if max_orders is not None and len(selections) > max_orders:
        logger.info(f"[{label}] capping {len(selections)} selection(s) to max_orders={max_orders}")
        selections = selections[:max_orders]

    api.submit_orders(game_id, selections)


@app.task(name="bot.plan", retry=3)
def plan(user_id, game_id):
    label = f"bot.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = ApiClient.for_user(user_id)
    try:
        data = fetch_context(api, game_id)
        _submit_orders_from_context(api, data, game_id, label)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="bot.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"bot.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = ApiClient.for_user(user_id)
    try:
        data = fetch_context(api, game_id)
        if data["game"].get("phase_confirmed"):
            logger.info(f"[{label}] orders already confirmed; skipping")
            return
        _submit_orders_from_context(api, data, game_id, label)
        api.confirm_phase(game_id)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="bot.reply", retry=3)
def reply(user_id, game_id, channel_id):
    label = f"bot.reply user={user_id} game={game_id} channel={channel_id}"
    logger.info(f"[{label}] invoked")

    api = ApiClient.for_user(user_id)
    try:
        data = fetch_context(api, game_id)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    builder = ContextBuilder(data).with_messages(channel_id=channel_id)
    system = load_prompt("reply_system.txt")
    instruction = load_prompt("reply_instruction.txt")
    user_content = "\n\n".join(
        part for part in [builder.build_shared(), builder.build_private(), instruction] if part
    )

    try:
        response_text = LLMClient(settings.ANTHROPIC_API_KEY).complete(
            system=system, messages=[{"role": "user", "content": user_content}]
        )
        reply_text = parse_reply(response_text)
    except LLMError as e:
        logger.info(f"[{label}] {e}; staying silent")
        return

    if not reply_text:
        logger.info(f"[{label}] no reply composed; staying silent")
        return

    try:
        api.post_message(game_id, channel_id, reply_text)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")
