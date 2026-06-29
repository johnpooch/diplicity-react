import logging

from procrastinate.contrib.django import app

from bot.actions import ReplyAction, SelectOrderAction
from bot.api_client import BotApiClient, BotApiError
from bot.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _submit_selected_orders(api, game_id, label):
    options = api.get_order_options(game_id)
    selections = LLMClient().run(SelectOrderAction(options))

    max_orders = api.get_max_orders(game_id)
    if max_orders is not None and len(selections) > max_orders:
        logger.info(f"[{label}] capping {len(selections)} selection(s) to max_orders={max_orders}")
        selections = selections[:max_orders]

    api.submit_orders(game_id, selections)


@app.task(name="bot.plan", retry=3)
def plan(user_id, game_id):
    label = f"bot.plan user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = BotApiClient.for_user(user_id)
    try:
        _submit_selected_orders(api, game_id, label)
    except BotApiError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="bot.finalize", retry=3)
def finalize(user_id, game_id):
    label = f"bot.finalize user={user_id} game={game_id}"
    logger.info(f"[{label}] invoked")

    api = BotApiClient.for_user(user_id)
    try:
        if api.is_phase_confirmed(game_id):
            logger.info(f"[{label}] orders already confirmed; skipping")
            return
        _submit_selected_orders(api, game_id, label)
        api.confirm_phase(game_id)
    except BotApiError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")


@app.task(name="bot.reply", retry=3)
def reply(user_id, game_id, channel_id):
    label = f"bot.reply user={user_id} game={game_id} channel={channel_id}"
    logger.info(f"[{label}] invoked")

    api = BotApiClient.for_user(user_id)
    try:
        messages = api.get_channel_messages(game_id, channel_id)
        reply_text = LLMClient().run(ReplyAction(messages))
        if not reply_text:
            logger.info(f"[{label}] no reply composed; staying silent")
            return
        api.post_message(game_id, channel_id, reply_text)
    except BotApiError as e:
        logger.error(f"[{label}] aborting: {e}")
        return

    logger.info(f"[{label}] completed")
