import logging

from django.conf import settings
from procrastinate.contrib.django import app

from agent.api_client import ApiClient, ApiClientError
from agent.context import fetch_context
from agent.fallback import first_legal_selections
from agent.orchestration import run_task
from bot_profile.models import BotProfile
from channel.models import Channel
from harness.exceptions import ParseError
from harness.tasks import ReplyTask, SelectOrdersTask
from harness.types import Persona, TaskContext
from inference.exceptions import InferenceError
from member.models import Member
from phase.models import Phase

logger = logging.getLogger(__name__)


def _persona(user_id) -> Persona | None:
    profile = BotProfile.objects.filter(user_id=user_id).first()
    if profile is None:
        return None
    return Persona(disposition=profile.disposition, voice=profile.voice)


def _phase(data):
    phase_id = data["game"].get("current_phase_id")
    if phase_id is None:
        return None
    return Phase.objects.filter(id=phase_id).first()


def _member(game_id, user_id):
    return Member.objects.filter(game_id=game_id, user_id=user_id).first()


def _submit_orders_from_context(api, data, game_id, user_id, label):
    task_ctx = TaskContext(persona=_persona(user_id))
    try:
        selections = run_task(
            SelectOrdersTask,
            context=data,
            task_ctx=task_ctx,
            phase=_phase(data),
            member=_member(game_id, user_id),
        )
    except (InferenceError, ParseError) as e:
        logger.info(f"[{label}] {e}; using first-legal selection")
        selections = first_legal_selections(data["orders"])
    else:
        covered = {selection[0] for selection in selections}
        missing = [s for s in first_legal_selections(data["orders"]) if s[0] not in covered]
        if missing:
            logger.info(f"[{label}] filling {len(missing)} unit(s) with first-legal selection")
            selections = selections + missing

    phase_states = data["phase_states"]
    max_orders = phase_states[0].get("max_orders") if phase_states else None
    if max_orders is not None and len(selections) > max_orders:
        logger.info(f"[{label}] capping {len(selections)} selection(s) to max_orders={max_orders}")
        selections = selections[:max_orders]

    api.submit_orders(game_id, selections)


@app.task(name="agent.plan", retry=3)
def plan(user_id, game_id):
    label = f"agent.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = ApiClient.for_user(user_id)
    try:
        data = fetch_context(api, game_id)
        _submit_orders_from_context(api, data, game_id, user_id, label)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="agent.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"agent.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = ApiClient.for_user(user_id)
    try:
        data = fetch_context(api, game_id)
        if data["game"].get("phase_confirmed"):
            logger.info(f"[{label}] orders already confirmed; skipping")
            return
        _submit_orders_from_context(api, data, game_id, user_id, label)
        api.confirm_phase(game_id)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="agent.reply", retry=3)
def reply(user_id, game_id, channel_id):
    label = f"agent.reply user={user_id} game={game_id} channel={channel_id}"
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

    member = _member(game_id, user_id)
    task_ctx = TaskContext(channel_id=channel_id, persona=_persona(user_id))
    try:
        reply_text = run_task(
            ReplyTask,
            context=data,
            task_ctx=task_ctx,
            phase=_phase(data),
            member=member,
            channel=Channel.objects.filter(id=channel_id).first(),
        )
    except (InferenceError, ParseError) as e:
        logger.info(f"[{label}] {e}; staying silent")
        return

    if not reply_text:
        logger.info(f"[{label}] no reply composed; staying silent")
        return

    max_chars = settings.CHAT_MESSAGE_MAX_CHARS
    if len(reply_text) > max_chars:
        logger.info(f"[{label}] reply is {len(reply_text)} chars; truncating to {max_chars}")
        reply_text = reply_text[:max_chars].rstrip()

    try:
        api.post_message(game_id, channel_id, reply_text)
    except ApiClientError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")
