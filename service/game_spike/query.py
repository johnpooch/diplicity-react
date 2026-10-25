from datetime import timedelta

from django.apps import apps
from django.db import models
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q, Subquery
from django.db.models.functions import Coalesce, Least
from django.utils import timezone

from common.constants import (
    Commitment,
    CommitmentRequirement,
    DeadlineMode,
    GameStatus,
    MemberKind,
    MovementPhaseDuration,
    PhaseFrequency,
    PhaseStatus,
    duration_to_seconds,
)

SHORT_DURATIONS = tuple(
    duration
    for duration, _ in MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES
    if duration_to_seconds(duration) < duration_to_seconds(MovementPhaseDuration.TWENTY_FOUR_HOURS)
)
RECENTLY_FINISHED_DAYS = 3


def _model(name):
    return apps.get_model("game_spike", name)


class GameQuerySet(models.QuerySet):
    def _seats_of(self, user):
        return _model("Member").objects.filter(game=OuterRef("pk"), user=user)

    def visible_to(self, user):
        if user.is_authenticated:
            return self
        return self.filter(private=False)

    def joined_by(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(Exists(self._seats_of(user)) | Q(game_master=user))

    def joinable_by(self, user):
        joinable = self.filter(status=GameStatus.PENDING, private=False)
        if not user.is_authenticated:
            return joinable
        return joinable.exclude(Exists(self._seats_of(user)))

    def eligible_for(self, user):
        if not user.is_authenticated:
            return self
        commitment = user.profile.commitment
        if commitment == Commitment.LOW:
            return self.none()
        if commitment == Commitment.HIGH:
            return self
        return self.filter(commitment_requirement=CommitmentRequirement.OPEN)

    def musterable(self):
        return self.filter(status=GameStatus.MUSTERING, sandbox=False, muster_deadline__isnull=False)

    def long_phased(self):
        return self.exclude(
            Q(deadline_mode=DeadlineMode.FIXED_TIME, movement_frequency=PhaseFrequency.HOURLY)
            | Q(deadline_mode=DeadlineMode.DURATION, movement_phase_duration__in=SHORT_DURATIONS)
        )

    def current_for(self, user):
        recently_finished = timezone.now() - timedelta(days=RECENTLY_FINISHED_DAYS)
        departed = (
            self._seats_of(user)
            .filter(kind=MemberKind.PLAYER)
            .filter(
                Q(eliminated_at__isnull=False, game__status=GameStatus.ACTIVE)
                | Q(eliminated_at__isnull=True)
                & (Q(civil_disorder_at__isnull=False) | Q(withdrawn_at__isnull=False) | Q(removed_at__isnull=False))
            )
        )
        return (
            self.joined_by(user)
            .filter(
                Q(status__in=(GameStatus.PENDING, GameStatus.MUSTERING, GameStatus.ACTIVE))
                | Q(sandbox=True)
                | Q(status__in=(GameStatus.COMPLETED, GameStatus.ABANDONED), finished_at__gte=recently_finished)
            )
            .exclude(Q(sandbox=False) & Exists(departed))
        )

    def finished_for(self, user):
        seats = self._seats_of(user).annotate(
            departed_at=Least("eliminated_at", "civil_disorder_at", "removed_at", "withdrawn_at")
        )
        return self.filter(sandbox=False).filter(
            Q(Exists(seats), status__in=(GameStatus.COMPLETED, GameStatus.ABANDONED))
            | Q(Exists(seats.filter(departed_at__isnull=False)), status=GameStatus.ACTIVE)
        )

    def with_ended_at(self, user):
        departed_at = (
            self._seats_of(user)
            .annotate(departed_at=Least("eliminated_at", "civil_disorder_at", "removed_at", "withdrawn_at"))
            .values("departed_at")[:1]
        )
        return self.annotate(ended_at=Coalesce(Subquery(departed_at), "finished_at"))

    def with_open_seats(self):
        return self.annotate(
            player_count=Count(
                "members",
                filter=Q(members__kind=MemberKind.PLAYER, members__replaced_by__isnull=True),
                distinct=True,
            ),
            seat_count=Count("variant__nations", filter=Q(variant__nations__non_playable=False), distinct=True),
            open_seats=F("seat_count") - F("player_count"),
        )

    def with_next_deadline(self):
        next_deadline = (
            _model("Phase")
            .objects.filter(game=OuterRef("pk"), status=PhaseStatus.ACTIVE)
            .order_by("-ordinal")
            .values("scheduled_resolution")[:1]
        )
        return self.annotate(next_deadline=Subquery(next_deadline))

    def with_viewer_eliminated(self, user):
        if not user.is_authenticated:
            return self.annotate(viewer_eliminated=models.Value(False))
        return self.annotate(viewer_eliminated=Exists(self._seats_of(user).filter(eliminated_at__isnull=False)))


class PhaseQuerySet(models.QuerySet):
    def armable(self):
        return self.filter(status=PhaseStatus.ACTIVE, game__sandbox=False, game__paused_at__isnull=True).exclude(
            game__status__in=(GameStatus.COMPLETED, GameStatus.ABANDONED)
        )


def members_prefetch():
    return Prefetch(
        "members",
        queryset=_model("Member")
        .objects.select_related("nation", "user__profile__uploaded_picture")
        .prefetch_related("nation_preferences__nation"),
    )


def phases_prefetch():
    return Prefetch("phases", queryset=_model("Phase").objects.defer("options"))


def victory_members_prefetch():
    return Prefetch("victory__members", queryset=_model("Member").objects.only("id"))


def game_queryset():
    return (
        _model("Game")
        .objects.select_related("variant", "victory", "game_master__profile__uploaded_picture")
        .prefetch_related(members_prefetch(), phases_prefetch(), victory_members_prefetch(), "variant__nations")
    )
