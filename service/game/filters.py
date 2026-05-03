import django_filters
from common.constants import GameStatus, MovementPhaseDuration

from .models import Game


class GameFilter(django_filters.FilterSet):
    mine = django_filters.BooleanFilter(method="filter_mine")
    can_join = django_filters.BooleanFilter(method="filter_can_join")
    sandbox = django_filters.BooleanFilter(method="filter_sandbox")
    status = django_filters.CharFilter(method="filter_status")
    variant = django_filters.CharFilter(field_name="variant_id")
    movement_phase_duration = django_filters.ChoiceFilter(
        choices=MovementPhaseDuration.MOVEMENT_PHASE_DURATION_CHOICES
    )

    class Meta:
        model = Game
        fields = []

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
