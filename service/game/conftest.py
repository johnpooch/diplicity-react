import pytest
from django.utils import timezone

from common.constants import (
    DeadlineMode,
    GameStatus,
    MemberKind,
    PhaseStatus,
    PhaseType,
)
from game.models import Game
from phase.models import PhaseState


@pytest.fixture
def seated_game_factory(
    db,
    primary_user,
    secondary_user,
    classical_variant,
    classical_england_nation,
    base_active_phase,
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
            eliminated_at=timezone.now() if seat == "eliminated" else None,
            civil_disorder_at=timezone.now() if seat == "civil_disorder" else None,
            removed_at=timezone.now() if seat in ("removed", "replaced") else None,
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


@pytest.fixture
def my_game_factory(db, primary_user, classical_variant, classical_england_nation):
    def _create(
        status=GameStatus.ACTIVE,
        user=None,
        seat=None,
        scheduled_resolution=None,
        has_possible_orders=True,
        orders_confirmed=False,
        orders=0,
        missed_deadline=False,
        created_at=None,
        **game_fields,
    ):
        user = user or primary_user
        seat = seat or {}
        is_game_master = seat.get("kind") == MemberKind.GAME_MASTER
        started = status not in (GameStatus.PENDING, GameStatus.MUSTERING)
        game_fields.setdefault("deadline_mode", DeadlineMode.DURATION)
        game = Game.objects.create(
            name=f"My Game {Game.objects.count()}",
            variant=classical_variant,
            status=status,
            game_master=user if is_game_master else None,
            **game_fields,
        )
        member = game.members.create(
            user=user,
            nation=classical_england_nation if started and not is_game_master else None,
            **seat,
        )
        ordinal = 1
        if missed_deadline:
            previous_phase = game.phases.create(
                variant=classical_variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.COMPLETED,
                ordinal=ordinal,
            )
            previous_phase.phase_states.create(
                member=member,
                has_possible_orders=True,
                orders_outcome=PhaseState.OrdersOutcome.NMR,
            )
            ordinal += 1
        phase_status = {
            GameStatus.PENDING: PhaseStatus.PENDING,
            GameStatus.MUSTERING: PhaseStatus.PENDING,
            GameStatus.ACTIVE: PhaseStatus.ACTIVE,
        }.get(status, PhaseStatus.COMPLETED)
        phase = game.phases.create(
            variant=classical_variant,
            season="Fall" if missed_deadline else "Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            status=phase_status,
            scheduled_resolution=scheduled_resolution,
            ordinal=ordinal,
        )
        if started and not is_game_master:
            phase_state = phase.phase_states.create(
                member=member,
                has_possible_orders=has_possible_orders,
                orders_confirmed=orders_confirmed,
            )
            for _ in range(orders):
                phase_state.orders.create()
        if created_at is not None:
            Game.objects.filter(id=game.id).update(created_at=created_at)
        return game

    return _create


@pytest.fixture
def primary_user_without_sandbox_games(db, primary_user):
    Game.objects.filter(sandbox=True, members__user=primary_user).delete()
