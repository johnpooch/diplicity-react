import logging
import time

from django.conf import settings
from procrastinate.contrib.django import app

from member.models import Member
from bot.api_client import ApiClient, ApiClientError
from bot.constants import LLMCallStage, LLMCallStatus
from bot.context import (
    ContextBuilder,
    fetch_context,
    first_legal_selections,
    parse_order_selections,
    parse_reply,
)
from bot.llm_client import LLMClient, LLMError
from bot.models import LLMCall
from bot.prompts import load_prompt

logger = logging.getLogger(__name__)


def _record_llm_call(
    *,
    game_id,
    user_id,
    phase_id,
    stage,
    system,
    user_content,
    status,
    model,
    response="",
    input_tokens=0,
    output_tokens=0,
    cache_read_tokens=0,
    cache_write_tokens=0,
    error_message="",
    latency_ms=None,
):
    if phase_id is None:
        logger.warning(f"[bot.llm] no phase id; skipping LLMCall record for stage={stage}")
        return
    try:
        member = Member.objects.filter(game_id=game_id, user_id=user_id).first()
        LLMCall.objects.create(
            phase_id=phase_id,
            member=member,
            stage=stage,
            status=status,
            model=model,
            system=system,
            user_content=user_content,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            error_message=error_message,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error(f"[bot.llm] failed to record LLMCall: {e}")


def _complete_and_record(*, system, user_content, stage, game_id, user_id, phase_id):
    messages = [{"role": "user", "content": user_content}]
    start = time.monotonic()
    try:
        result = LLMClient(settings.ANTHROPIC_API_KEY).complete(system=system, messages=messages)
    except LLMError as e:
        _record_llm_call(
            game_id=game_id,
            user_id=user_id,
            phase_id=phase_id,
            stage=stage,
            system=system,
            user_content=user_content,
            status=LLMCallStatus.ERROR,
            model=settings.BOT_LLM_MODEL,
            error_message=str(e),
            latency_ms=int((time.monotonic() - start) * 1000),
        )
        raise

    _record_llm_call(
        game_id=game_id,
        user_id=user_id,
        phase_id=phase_id,
        stage=stage,
        system=system,
        user_content=user_content,
        status=LLMCallStatus.SUCCESS,
        model=result.model,
        response=result.text,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cache_read_tokens=result.cache_read_tokens,
        cache_write_tokens=result.cache_write_tokens,
        latency_ms=int((time.monotonic() - start) * 1000),
    )
    return result.text


def _submit_orders_from_context(api, data, game_id, user_id, label, stage):
    builder = (
        ContextBuilder(data)
        .with_game_state()
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
        response_text = _complete_and_record(
            system=system,
            user_content=user_content,
            stage=stage,
            game_id=game_id,
            user_id=user_id,
            phase_id=data["game"].get("current_phase_id"),
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
        _submit_orders_from_context(api, data, game_id, user_id, label, LLMCallStage.PLAN)
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
        _submit_orders_from_context(api, data, game_id, user_id, label, LLMCallStage.COMMIT)
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

    channel = next((c for c in data["channels"] if c["id"] == channel_id), None)
    if channel is not None:
        limit = channel.get("message_limit")
        count = channel.get("member_message_count")
        if limit is not None and count is not None and count >= limit:
            logger.info(f"[{label}] message cap reached ({count}/{limit}); staying silent")
            return

    builder = (
        ContextBuilder(data)
        .with_game_state()
        .with_messages(channel_id=channel_id)
    )
    system = load_prompt("reply_system.txt")
    instruction = load_prompt("reply_instruction.txt")
    user_content = "\n\n".join(
        part for part in [builder.build_shared(), builder.build_private(), instruction] if part
    )

    try:
        response_text = _complete_and_record(
            system=system,
            user_content=user_content,
            stage=LLMCallStage.REPLY,
            game_id=game_id,
            user_id=user_id,
            phase_id=data["game"].get("current_phase_id"),
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
