from common.constants import (
    ABANDONMENT_NMR_THRESHOLD,
    MemberOutcomeState,
    PhaseStatus,
    PhaseType,
)
from member.models import Member


def classify_outcomes_for_finished_game(game):
    if game.sandbox:
        return

    movement_phases = list(
        game.phases.filter(
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.COMPLETED,
        )
        .order_by("ordinal")
        .prefetch_related("units", "phase_states__orders")
    )

    members = list(game.members.exclude(is_game_master=True).select_related("nation"))

    for member in members:
        member.outcome_state = _classify_member(member, movement_phases)

    Member.objects.bulk_update(members, ["outcome_state"])

    if not game.private:
        from user_profile.utils import recompute_reliability_counters
        user_ids = {m.user_id for m in members if m.user_id is not None}
        for user_id in user_ids:
            recompute_reliability_counters(user_id)


def kick_inactive_members(game):
    if game.sandbox:
        return []

    recent_movement_phases = list(
        game.phases.filter(
            status=PhaseStatus.COMPLETED,
            type=PhaseType.MOVEMENT,
        )
        .order_by("-ordinal")[:ABANDONMENT_NMR_THRESHOLD]
        .prefetch_related("units", "phase_states__orders")
    )

    if len(recent_movement_phases) < ABANDONMENT_NMR_THRESHOLD:
        return []

    candidates = list(
        game.members.filter(kicked=False, is_game_master=False)
        .exclude(nation__isnull=True)
        .select_related("nation")
    )

    members_to_kick = [
        member
        for member in candidates
        if _all_phases_are_nmr_for_member(member, recent_movement_phases)
    ]

    if members_to_kick:
        for member in members_to_kick:
            member.kicked = True
        Member.objects.bulk_update(members_to_kick, ["kicked"])

    return members_to_kick


def _all_phases_are_nmr_for_member(member, phases):
    for phase in phases:
        had_units = any(unit.nation_id == member.nation_id for unit in phase.units.all())
        if not had_units:
            return False

        member_phase_state = next(
            (ps for ps in phase.phase_states.all() if ps.member_id == member.id),
            None,
        )
        if member_phase_state is None:
            return False

        if any(member_phase_state.orders.all()):
            return False

    return True


def _classify_member(member, movement_phases):
    if member.kicked:
        return MemberOutcomeState.ABANDONED

    if member.nation_id is None:
        return MemberOutcomeState.COMPLETED

    longest_streak = _longest_consecutive_nmr_streak(member, movement_phases)
    if longest_streak >= ABANDONMENT_NMR_THRESHOLD:
        return MemberOutcomeState.ABANDONED

    return MemberOutcomeState.COMPLETED


def _longest_consecutive_nmr_streak(member, movement_phases):
    longest = 0
    current = 0

    for phase in movement_phases:
        had_units = any(unit.nation_id == member.nation_id for unit in phase.units.all())
        if not had_units:
            current = 0
            continue

        member_phase_state = next(
            (ps for ps in phase.phase_states.all() if ps.member_id == member.id),
            None,
        )
        if member_phase_state is None:
            current = 0
            continue

        submitted_orders = any(True for _ in member_phase_state.orders.all())
        if submitted_orders:
            current = 0
        else:
            current += 1
            if current > longest:
                longest = current

    return longest
