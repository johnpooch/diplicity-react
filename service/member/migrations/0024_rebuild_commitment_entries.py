from datetime import datetime, timezone

from django.db import migrations
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce

from common.constants import (
    CommitmentEvent,
    MemberKind,
    PhaseStatus,
    PhaseType,
    UserKind,
)

CIVIL_DISORDER_DETECTED_FROM = datetime(2026, 4, 10, tzinfo=timezone.utc)
REMOVAL_TIMESTAMP_TRUSTED_FROM = datetime(2026, 10, 12, tzinfo=timezone.utc)
CIVIL_DISORDER_NMR_TRIGGER = 2
RECEIVED = "received"
NMR = "nmr"


def _civil_disorder_trigger(states):
    last_submitted = max(
        (index for index, (outcome, _, _) in enumerate(states) if outcome == RECEIVED),
        default=-1,
    )
    consecutive_movement_nmrs = 0
    for index, (outcome, phase_type, _) in enumerate(states):
        if phase_type != PhaseType.MOVEMENT:
            continue
        if outcome != NMR:
            consecutive_movement_nmrs = 0
            continue
        consecutive_movement_nmrs += 1
        if (
            consecutive_movement_nmrs >= CIVIL_DISORDER_NMR_TRIGGER
            and index > last_submitted
        ):
            return index
    return None


def _withdrawal_kind(withdrawn_at, phases):
    in_progress = [year for year, created_at in phases if created_at <= withdrawn_at]
    if in_progress and in_progress[-1] == phases[0][0]:
        return CommitmentEvent.EARLY_WITHDRAWAL
    return CommitmentEvent.LATE_WITHDRAWAL


def _kinds(member, states, phases):
    if (
        member.removed_at is not None
        and member.removed_at >= REMOVAL_TIMESTAMP_TRUSTED_FROM
    ):
        states = [state for state in states if state[2] <= member.removed_at]

    trigger = _civil_disorder_trigger(states)
    entered_civil_disorder = trigger is not None and (
        member.civil_disorder_at is not None
        or states[trigger][2] < CIVIL_DISORDER_DETECTED_FROM
    )
    if entered_civil_disorder:
        states = states[: trigger + 1]

    kinds = [
        CommitmentEvent.SUBMITTED if outcome == RECEIVED else CommitmentEvent.NMR
        for outcome, _, _ in states
        if outcome is not None
    ]
    if entered_civil_disorder or member.civil_disorder_at is not None:
        kinds.append(CommitmentEvent.CIVIL_DISORDER)
    if member.withdrawn_at is not None:
        kinds.append(_withdrawal_kind(member.withdrawn_at, phases))
    if (
        member.game.muster_required
        and member.mustered_at is None
        and member.removed_at is not None
    ):
        kinds.append(CommitmentEvent.MUSTER_NO_SHOW)
    return kinds


def rebuild_commitment_entries(apps, schema_editor):
    CommitmentEntry = apps.get_model("member", "CommitmentEntry")
    Member = apps.get_model("member", "Member")
    Phase = apps.get_model("phase", "Phase")
    PhaseState = apps.get_model("phase", "PhaseState")

    CommitmentEntry.objects.all().delete()

    members = list(
        Member.objects.filter(
            kind=MemberKind.PLAYER,
            game__sandbox=False,
            game__private=False,
            user__profile__kind=UserKind.HUMAN,
        ).select_related("game")
    )

    next_phase_created_at = (
        Phase.objects.filter(
            game_id=OuterRef("phase__game_id"),
            ordinal__gt=OuterRef("phase__ordinal"),
        )
        .order_by("ordinal")
        .values("created_at")[:1]
    )
    states = (
        PhaseState.objects.filter(
            member__kind=MemberKind.PLAYER,
            member__game__sandbox=False,
            member__game__private=False,
            member__user__profile__kind=UserKind.HUMAN,
            has_possible_orders=True,
            phase__status=PhaseStatus.COMPLETED,
        )
        .annotate(
            resolved_at=Coalesce(
                Subquery(next_phase_created_at), F("phase__updated_at")
            )
        )
        .order_by("member_id", "phase__ordinal")
        .values_list("member_id", "orders_outcome", "phase__type", "resolved_at")
    )
    states_by_member = {}
    for member_id, *state in states.iterator(chunk_size=10000):
        states_by_member.setdefault(member_id, []).append(tuple(state))

    phases_by_game = {}
    for game_id, year, created_at in (
        Phase.objects.filter(
            game_id__in={member.game_id for member in members if member.withdrawn_at}
        )
        .order_by("ordinal", "id")
        .values_list("game_id", "year", "created_at")
    ):
        phases_by_game.setdefault(game_id, []).append((year, created_at))

    CommitmentEntry.objects.bulk_create(
        [
            CommitmentEntry(member=member, kind=kind)
            for member in members
            for kind in _kinds(
                member,
                states_by_member.get(member.id, []),
                phases_by_game.get(member.game_id, []),
            )
        ],
        batch_size=10000,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("member", "0023_commitmententry_member_kind_idx"),
        ("phase", "0024_phase_latest_indexes"),
        ("game", "0027_remove_game_min_reliability"),
        ("user_profile", "0012_userprofilepicturecontent"),
    ]

    operations = [
        migrations.RunPython(rebuild_commitment_entries, migrations.RunPython.noop),
    ]
