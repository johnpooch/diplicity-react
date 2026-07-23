from common.constants import Commitment, CommitmentRequirement, PhaseStatus, PhaseType
from phase.models import PhaseState

COMMITMENT_PHASE_WINDOW = 10
COMMITMENT_HIGH_NMR_THRESHOLD = 0.1
COMMITMENT_LOW_NMR_THRESHOLD = 0.5
COMMITMENT_LOW_NMR_FLOOR = 2
CIVIL_DISORDER_NMR_TRIGGER = 2


def score_commitment(outcomes):
    rated = outcomes[:COMMITMENT_PHASE_WINDOW]
    if not rated:
        return Commitment.UNDEFINED

    nmr_count = sum(1 for outcome in rated if outcome == PhaseState.OrdersOutcome.NMR)
    rate = nmr_count / len(rated)

    if rate >= COMMITMENT_LOW_NMR_THRESHOLD and nmr_count >= COMMITMENT_LOW_NMR_FLOOR:
        return Commitment.LOW
    if len(rated) < COMMITMENT_PHASE_WINDOW:
        return Commitment.UNDEFINED
    if rate <= COMMITMENT_HIGH_NMR_THRESHOLD:
        return Commitment.HIGH
    return Commitment.MEDIUM


def clamp_post_civil_disorder(states):
    rated = []
    consecutive_movement_nmrs = 0
    for state in states:
        rated.append(state)
        if state.phase.type != PhaseType.MOVEMENT:
            continue
        if state.orders_outcome == PhaseState.OrdersOutcome.NMR:
            consecutive_movement_nmrs += 1
            if consecutive_movement_nmrs >= CIVIL_DISORDER_NMR_TRIGGER:
                break
        else:
            consecutive_movement_nmrs = 0
    return rated


def get_rated_outcomes(user):
    states = (
        PhaseState.objects.filter(
            member__user=user,
            member__kicked=False,
            has_possible_orders=True,
            orders_outcome__isnull=False,
            phase__status=PhaseStatus.COMPLETED,
            phase__game__sandbox=False,
            phase__game__private=False,
        )
        .select_related("phase")
        .order_by("member_id", "phase__ordinal")
    )

    states_by_member = {}
    for state in states:
        states_by_member.setdefault(state.member_id, []).append(state)

    rated = []
    for member_states in states_by_member.values():
        rated.extend(clamp_post_civil_disorder(member_states))

    rated.sort(
        key=lambda state: (state.phase.updated_at, state.phase.ordinal, state.id),
        reverse=True,
    )
    return [state.orders_outcome for state in rated]


def recompute_commitment(user):
    profile = user.profile
    profile.commitment = score_commitment(get_rated_outcomes(user))
    profile.save(update_fields=["commitment", "updated_at"])
    return profile.commitment


def commitment_allows_requirement(commitment, commitment_requirement):
    if commitment == Commitment.LOW:
        return False
    if commitment_requirement == CommitmentRequirement.COMMITTED:
        return commitment == Commitment.HIGH
    return True
