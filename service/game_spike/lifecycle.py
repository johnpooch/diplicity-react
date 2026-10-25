from datetime import timedelta

from django.apps import apps
from django.utils import timezone

from adjudicator import service as adjudication_service
from common.constants import DeniedReason, GameStatus, PhaseStatus, duration_to_seconds
from common.lifecycle import transition
from common.policies import ALLOW, deny

from .legacy import legacy_phase


def _active_unpaused(game):
    if game.status != GameStatus.ACTIVE:
        return deny(DeniedReason.GAME_NOT_ACTIVE)
    if game.is_paused:
        return deny(DeniedReason.GAME_PAUSED)
    return ALLOW


def _active_paused(game):
    if game.status != GameStatus.ACTIVE:
        return deny(DeniedReason.GAME_NOT_ACTIVE)
    if not game.is_paused:
        return deny(DeniedReason.GAME_NOT_PAUSED)
    return ALLOW


def _deadline_extendable(game):
    decision = _active_unpaused(game)
    if not decision:
        return decision
    phase = game.current_phase
    if phase is None or phase.scheduled_resolution is None:
        return deny(DeniedReason.NO_SCHEDULED_RESOLUTION)
    return ALLOW


def _seated(member):
    if member.removed:
        return deny(DeniedReason.SEAT_VACATED)
    return ALLOW


class GameLifecycle:
    @transition(source=GameStatus.PENDING, target=GameStatus.MUSTERING, reason=DeniedReason.GAME_NOT_PENDING)
    def enter_mustering(self):
        self.muster_deadline = timezone.now() + timedelta(seconds=self.muster_window_seconds)

    @transition(
        source=(GameStatus.PENDING, GameStatus.MUSTERING),
        target=GameStatus.ACTIVE,
        stamp="started_at",
        reason=DeniedReason.GAME_STARTED,
    )
    def start(self):
        phase = self.current_phase
        phase.options = adjudication_service.start(legacy_phase(phase))["options"]
        phase.status = PhaseStatus.ACTIVE
        phase.scheduled_resolution = self.scheduled_resolution(phase.type, timezone.now(), is_first_phase=True)
        phase.save()

        players = self.players
        assignments = self.nation_assignments(players, self.playable_nations)
        now = timezone.now()
        for member in players:
            member.nation = assignments[member.id]
            member.nmr_extensions_remaining = self.nmr_extensions_allowed
            member.updated_at = now
        self.members.model.objects.bulk_update(players, ["nation", "nmr_extensions_remaining", "updated_at"])

        nations_with_orders = phase.nations_with_possible_orders
        phase.phase_states.model.objects.bulk_create(
            [
                phase.phase_states.model(
                    phase=phase, member=member, has_possible_orders=member.nation.name in nations_with_orders
                )
                for member in players
            ]
        )
        self.muster_deadline = None

    @transition(
        source=GameStatus.ACTIVE, target=GameStatus.COMPLETED, stamp="finished_at", reason=DeniedReason.GAME_NOT_ACTIVE
    )
    def complete(self):
        for phase in self.phases.exclude(status=PhaseStatus.COMPLETED):
            phase.status = PhaseStatus.COMPLETED
            phase.scheduled_resolution = None
            phase.save(update_fields=["status", "scheduled_resolution", "updated_at"])

    @transition(guard=_active_unpaused, stamp="paused_at")
    def pause(self):
        pass

    @transition(guard=_active_paused)
    def unpause(self):
        phase = self.current_phase
        if phase is not None and phase.scheduled_resolution is not None:
            phase.scheduled_resolution += timezone.now() - self.paused_at
            phase.save(update_fields=["scheduled_resolution", "updated_at"])
        self.paused_at = None

    @transition(guard=_deadline_extendable)
    def extend_deadline(self, duration):
        phase = self.current_phase
        phase.scheduled_resolution += timedelta(seconds=duration_to_seconds(duration))
        phase.save(update_fields=["scheduled_resolution", "updated_at"])


class MemberLifecycle:
    @transition(guard=_seated, stamp="removed_at")
    def remove(self):
        states = self.phase_states.filter(phase__status=PhaseStatus.ACTIVE)
        apps.get_model("game_spike", "Order").objects.filter(phase_state__in=states).delete()
        states.update(orders_confirmed=True)
