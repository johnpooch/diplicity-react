import django_filters
from django.db.models import F

from common.constants import GameStatus, MovementPhaseDuration
from common.filters import FilterSet

from .models import Game

FASTEST_START_MIN_PLAYERS = 3


class GameOrdering:
    SLOTS_REMAINING = "slots_remaining"
    DEADLINE = "deadline"
    FINISHED = "finished"
    CREATED = "created"

    CHOICES = (
        (SLOTS_REMAINING, "Slots remaining"),
        (DEADLINE, "Deadline"),
        (FINISHED, "Finished"),
        (CREATED, "Created"),
    )


class StatusInFilter(django_filters.BaseInFilter, django_filters.ChoiceFilter):
    pass


class GameFilterSet(FilterSet):
    ordering = django_filters.ChoiceFilter(choices=GameOrdering.CHOICES, method="filter_ordering")

    class Meta:
        model = Game
        fields = []

    @property
    def qs(self):
        return super().qs.visible_to(self.request.user)

    def filter_mine(self, queryset, name, value):
        return queryset.joined_by(self.request.user) if value else queryset

    def filter_can_join(self, queryset, name, value):
        return queryset.joinable_by(self.request.user) if value else queryset

    def filter_eligible_only(self, queryset, name, value):
        return queryset.eligible_for(self.request.user) if value else queryset

    def filter_long_phased(self, queryset, name, value):
        return queryset.long_phased() if value else queryset

    def filter_min_players(self, queryset, name, value):
        return queryset.with_open_seats().filter(player_count__gte=value)

    def filter_ordering(self, queryset, name, value):
        if value == GameOrdering.SLOTS_REMAINING:
            return queryset.with_open_seats().order_by("open_seats", "-created_at")
        if value == GameOrdering.DEADLINE:
            return (
                queryset.with_next_deadline()
                .with_viewer_eliminated(self.request.user)
                .order_by("sandbox", "viewer_eliminated", F("next_deadline").asc(nulls_last=True), "-created_at")
            )
        if value == GameOrdering.FINISHED:
            return queryset.order_by(F("finished_at").desc(nulls_last=True), "-created_at")
        return queryset.order_by("-created_at")


class GameFilter(GameFilterSet):
    defaults = {"sandbox": "false", "ordering": GameOrdering.CREATED}

    mine = django_filters.BooleanFilter(method="filter_mine")
    can_join = django_filters.BooleanFilter(method="filter_can_join")
    eligible_only = django_filters.BooleanFilter(method="filter_eligible_only")
    sandbox = django_filters.BooleanFilter()
    status = StatusInFilter(choices=GameStatus.STATUS_CHOICES)
    variant = django_filters.CharFilter(field_name="variant_id")
    movement_phase_duration = django_filters.ChoiceFilter(choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES)


class SimilarGameFilter(GameFilterSet):
    defaults = {"can_join": "true", "ordering": GameOrdering.SLOTS_REMAINING}

    can_join = django_filters.BooleanFilter(method="filter_can_join")
    variant = django_filters.CharFilter(field_name="variant_id", required=True)
    movement_phase_duration = django_filters.ChoiceFilter(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES, required=True
    )


class FastestGameFilter(GameFilterSet):
    defaults = {
        "can_join": "true",
        "long_phased": "true",
        "min_players": FASTEST_START_MIN_PLAYERS,
        "ordering": GameOrdering.SLOTS_REMAINING,
    }

    can_join = django_filters.BooleanFilter(method="filter_can_join")
    long_phased = django_filters.BooleanFilter(method="filter_long_phased")
    min_players = django_filters.NumberFilter(method="filter_min_players")


class MyCurrentGamesFilter(FilterSet):
    class Meta:
        model = Game
        fields = []

    @property
    def qs(self):
        return super().qs.current_for(self.request.user)


class MyFinishedGamesFilter(FilterSet):
    defaults = {"ordering": GameOrdering.FINISHED}

    ordering = django_filters.ChoiceFilter(choices=((GameOrdering.FINISHED, "Finished"),), method="filter_ordering")

    class Meta:
        model = Game
        fields = []

    @property
    def qs(self):
        return super().qs.finished_for(self.request.user)

    def filter_ordering(self, queryset, name, value):
        return queryset.with_ended_at(self.request.user).order_by(
            F("ended_at").desc(nulls_last=True), "-created_at", "-id"
        )
