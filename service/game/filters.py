import django_filters
from django.db.models import Count, F

from common.constants import (
    GameStatus,
    MinReliability,
    MovementPhaseDuration,
    ReliabilityTier,
)

from .models import Game


class GameFilter(django_filters.FilterSet):
    mine = django_filters.BooleanFilter(method="filter_mine")
    can_join = django_filters.BooleanFilter(method="filter_can_join")
    include_ineligible = django_filters.BooleanFilter(method="filter_noop")
    sandbox = django_filters.BooleanFilter(method="filter_sandbox")
    status = django_filters.CharFilter(method="filter_status")
    variant = django_filters.CharFilter(field_name="variant_id")
    movement_phase_duration = django_filters.ChoiceFilter(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES
    )
    min_reliability = django_filters.ChoiceFilter(
        choices=MinReliability.MIN_RELIABILITY_CHOICES
    )
    ordering = django_filters.CharFilter(method="filter_ordering")

    class Meta:
        model = Game
        fields = []

    def filter_noop(self, queryset, name, value):
        return queryset

    def filter_mine(self, queryset, name, value):
        if value:
            if not self.request.user.is_authenticated:
                return queryset.none()
            return queryset.filter(members__user=self.request.user).distinct()
        return queryset

    def filter_can_join(self, queryset, name, value):
        if value:
            queryset = queryset.filter(status=GameStatus.PENDING, private=False)
            if self.request.user.is_authenticated:
                queryset = queryset.exclude(members__user=self.request.user)
                include_ineligible = self.data.get("include_ineligible") in ("true", "True", "1")
                if not include_ineligible:
                    profile = getattr(self.request.user, "profile", None)
                    if profile is not None:
                        tier = profile.reliability_tier
                        if tier == ReliabilityTier.UNRELIABLE:
                            queryset = queryset.filter(min_reliability=MinReliability.OPEN)
                        elif tier == ReliabilityTier.NEW_PLAYER:
                            queryset = queryset.filter(
                                min_reliability__in=[
                                    MinReliability.OPEN,
                                    MinReliability.RELIABLE_AND_NEW,
                                ]
                            )
            return queryset
        return queryset

    def filter_sandbox(self, queryset, name, value):
        return queryset.filter(sandbox=value)

    def filter_status(self, queryset, name, value):
        statuses = [s.strip() for s in value.split(",") if s.strip()]
        valid = {s[0] for s in GameStatus.STATUS_CHOICES}
        statuses = [s for s in statuses if s in valid]
        if statuses:
            return queryset.filter(status__in=statuses)
        return queryset

    def filter_ordering(self, queryset, name, value):
        if value == "slots_remaining":
            # No kick filter on members: pending games only lose members on
            # account deletion, so every member row counts toward fill.
            return queryset.annotate(
                member_count=Count("members", distinct=True),
                nation_count=Count("variant__nations", distinct=True),
                slots_remaining=F("nation_count") - F("member_count"),
            ).order_by("slots_remaining", "-created_at")
        return queryset
