import logging

from django.conf import settings
from procrastinate.contrib.django import app

from agent.api_client import ApiClient, ApiClientError
from agent.constants import AgentTaskKind, AgentTaskStatus
from agent.context import fetch_context
from agent.fallback import first_legal_options
from agent.models import AgentTask
from agent.orders import option_to_selected
from agent.orchestration import run_reply, run_select_orders
from bot_profile.models import BotProfile
from channel.models import Channel
from harness.adapter import orders_to_options
from harness.exceptions import ContextError, ParsingError
from harness.types import Persona
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
    options = orders_to_options(data["orders"])
    try:
        orders = run_select_orders(
            data=data,
            persona=_persona(user_id),
            phase=_phase(data),
            member=_member(game_id, user_id),
        )
    except (ContextError, InferenceError, ParsingError) as e:
        logger.info(f"[{label}] {e}; using first-legal selection")
        orders = first_legal_options(options)
    else:
        covered = {order["source"] for order in orders}
        missing = [option for option in first_legal_options(options) if option["source"] not in covered]
        if missing:
            logger.info(f"[{label}] filling {len(missing)} unit(s) with first-legal selection")
            orders = orders + missing

    phase_states = data["phase_states"]
    max_orders = phase_states[0].get("max_orders") if phase_states else None
    if max_orders is not None and len(orders) > max_orders:
        logger.info(f"[{label}] capping {len(orders)} selection(s) to max_orders={max_orders}")
        orders = orders[:max_orders]

    api.submit_orders(game_id, [option_to_selected(order) for order in orders])


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

    try:
        reply_text = run_reply(
            data=data,
            channel_id=channel_id,
            persona=_persona(user_id),
            phase=_phase(data),
            member=_member(game_id, user_id),
            channel=Channel.objects.filter(id=channel_id).first(),
        )
    except (ContextError, InferenceError, ParsingError) as e:
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


def _dispatch(task):
    member = task.member
    if task.kind == AgentTaskKind.PLAN:
        plan(member.user_id, member.game_id)
    elif task.kind == AgentTaskKind.FINALIZE:
        finalize(member.user_id, member.game_id)
    elif task.kind == AgentTaskKind.REPLY:
        reply(member.user_id, member.game_id, task.message.channel_id)


@app.task(name="agent.run", retry=3)
def run(agent_task_id):
    label = f"agent.run task={agent_task_id}"
    task = AgentTask.objects.select_related("member", "message").filter(id=agent_task_id).first()
    if task is None:
        logger.error(f"[{label}] no agent task found; skipping")
        return
    if task.status == AgentTaskStatus.SUCCEEDED:
        logger.info(f"[{label}] already succeeded; skipping")
        return

    logger.info(f"[{label}] running {task.kind} for member {task.member_id}")
    task.mark_running()
    try:
        _dispatch(task)
    except Exception as e:
        task.mark_failed(e)
        logger.error(f"[{label}] failed: {e}")
        raise
    task.mark_succeeded()
    logger.info(f"[{label}] completed")


@app.periodic(cron="* * * * *")
@app.task(name="agent.reconcile")
def reconcile(timestamp):
    tasks = AgentTask.objects.reconcile()
    if tasks:
        logger.info(f"[agent.reconcile] re-drove {len(tasks)} stalled task(s)")
