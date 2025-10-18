import django_filters
from common.constants import GameStatus

from .models import Game


class GameFilter(django_filters.FilterSet):
    mine = django_filters.BooleanFilter(method="filter_mine")
    can_join = django_filters.BooleanFilter(method="filter_can_join")
    sandbox = django_filters.BooleanFilter(method="filter_sandbox")

    class Meta:
        model = Game
        fields = []

    def filter_mine(self, queryset, name, value):
        if value:
            return queryset.filter(members__user=self.request.user)
        return queryset

    def filter_can_join(self, queryset, name, value):
        if value:
            return queryset.filter(
                status=GameStatus.PENDING,
                private=False
            ).exclude(members__user=self.request.user)
        return queryset

    def filter_sandbox(self, queryset, name, value):
        return queryset.filter(sandbox=value)
