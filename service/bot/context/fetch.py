import logging

from bot.api_client import ApiClient, ApiClientError
from bot.types import ContextData

logger = logging.getLogger(__name__)


def fetch_context(api: ApiClient, game_id) -> ContextData:
    game = api.get_game(game_id)
    current_phase_id = game.get("current_phase_id")
    phase = api.get_phase(game_id, current_phase_id) if current_phase_id else {}
    variant_id = game.get("variant_id")
    variant = {}
    if variant_id:
        try:
            variant = api.get_variant(variant_id)
        except ApiClientError as e:
            logger.warning(f"[bot.context] variant fetch failed ({e}); continuing without tactical annotations")
    data: ContextData = {
        "orders": api.get_order_options(game_id),
        "phase_states": api.get_phase_states(game_id),
        "game": game,
        "phase": phase,
        "channels": api.get_channels(game_id),
        "variant": variant,
    }
    logger.info(
        f"[bot.context] fetched context for game {game_id}: "
        f"{len(data['orders'])} order option(s), {len(data['channels'])} channel(s), "
        f"{len(phase.get('units', []))} unit(s), {len(variant.get('provinces', []))} province(s)"
    )
    return data
