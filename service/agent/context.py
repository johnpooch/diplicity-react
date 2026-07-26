import logging

from agent.api_client import ApiClient
from harness_v2.types import ApiData

logger = logging.getLogger(__name__)


def fetch_context(api: ApiClient, game_id) -> ApiData:
    game = api.get_game(game_id)
    current_phase_id = game.get("current_phase_id")
    phase = api.get_phase(game_id, current_phase_id) if current_phase_id else {}
    variant_id = game.get("variant_id")
    variant = api.get_variant(variant_id) if variant_id else {}
    data: ApiData = {
        "game": game,
        "phase": phase,
        "phase_states": api.get_phase_states(game_id),
        "orders": api.get_order_options(game_id),
        "variant": variant,
        "channels": api.get_channels(game_id),
    }
    logger.info(
        f"[agent.context] fetched context for game {game_id}: "
        f"{len(data['orders'])} order option(s), {len(data['channels'])} channel(s), "
        f"{len(phase.get('units', []))} unit(s), {len(variant.get('provinces', []))} province(s)"
    )
    return data
