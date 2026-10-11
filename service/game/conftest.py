import pytest
from django.utils import timezone

from common.constants import DeadlineMode, GameStatus
from game.models import Game


@pytest.fixture
def seated_game_factory(
    db, primary_user, secondary_user, classical_variant, classical_england_nation, base_active_phase
):
    def _create(seat):
        game = Game.objects.create(
            name=f"Seated Game {seat}",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.DURATION,
            sandbox=seat == "sandbox",
        )
        phase = base_active_phase(game)
        member = game.members.create(
            user=secondary_user if seat == "spectator" else primary_user,
            nation=classical_england_nation,
            sandbox=seat == "sandbox",
            eliminated=seat == "eliminated",
            civil_disorder=seat == "civil_disorder",
            kicked=seat in ("removed", "replaced"),
            withdrawn_at=timezone.now() if seat == "withdrawn" else None,
        )
        if seat == "replaced":
            member.replaced_by = game.members.create(user=secondary_user)
            member.save(update_fields=["replaced_by"])
        phase_state = phase.phase_states.create(
            member=member,
            has_possible_orders=seat not in ("eliminated", "replaced"),
            orders_confirmed=member.vacant or seat == "orders_confirmed",
        )
        if seat == "orders_not_confirmed":
            phase_state.orders.create()
        return game

    return _create
