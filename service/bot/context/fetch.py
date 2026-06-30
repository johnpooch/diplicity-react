import logging

from bot.api_client import ApiClient
from bot.types import ContextData

logger = logging.getLogger(__name__)


def fetch_context(api: ApiClient, game_id) -> ContextData:
    data: ContextData = {
        "orders": api.get_order_options(game_id),
        "phase_states": api.get_phase_states(game_id),
        "game": api.get_game(game_id),
        "channels": api.get_channels(game_id),
    }
    logger.info(
        f"[bot.context] fetched context for game {game_id}: "
        f"{len(data['orders'])} order option(s), {len(data['channels'])} channel(s)"
    )
    return data
