import logging

from django.db import transaction

from common.constants import OrderType, PhaseStatus, PhaseType
from phase.tasks import resolve_phase

from bot.game_client import BotGameClient
from bot.utils import get_bot_user

logger = logging.getLogger(__name__)


def _option_to_selected(option):
    order_type = option["order_type"]["id"]
    selected = [option["source"]["id"], order_type]

    if order_type == OrderType.BUILD:
        selected.append(option["unit_type"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.MOVE, OrderType.MOVE_VIA_CONVOY):
        selected.append(option["target"]["id"])
        if option["named_coast"]:
            selected.append(option["named_coast"]["id"])
    elif order_type in (OrderType.SUPPORT, OrderType.CONVOY):
        selected.append(option["aux"]["id"])
        selected.append(option["target"]["id"])

    return selected


def _select_first_legal_orders(options, phase_state):
    first_by_source = {}
    for option in options:
        source_id = option["source"]["id"]
        if source_id not in first_by_source:
            first_by_source[source_id] = option

    selected_options = list(first_by_source.values())

    if phase_state.phase.type == PhaseType.ADJUSTMENT:
        max_orders = phase_state.max_allowed_adjustment_orders()
        selected_options = selected_options[:max_orders]

    return [_option_to_selected(option) for option in selected_options]


def play_bot_turn(phase):
    if phase.status != PhaseStatus.ACTIVE:
        return

    bot_user = get_bot_user()
    phase_states = phase.phase_states.filter(member__user=bot_user).select_related(
        "member__nation", "member__user"
    )

    for phase_state in phase_states:
        if not phase_state.has_possible_orders or phase_state.orders_confirmed:
            continue

        client = BotGameClient(phase, phase_state.member)
        selections = _select_first_legal_orders(client.get_options(), phase_state)

        with transaction.atomic():
            client.submit_orders(selections)
            phase_state.orders_confirmed = True
            phase_state.save()
            resolve_phase.configure(
                lock=f"resolve-game-{phase.game_id}",
            ).defer(phase_id=phase.id)

        logger.info(
            f"Bot submitted {len(selections)} orders for phase {phase.id} "
            f"(game {phase.game_id}, nation {phase_state.member.nation.name})"
        )
