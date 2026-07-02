import django_filters

from bot.models import LLMCall


class LLMCallFilter(django_filters.FilterSet):
    game = django_filters.CharFilter(field_name="phase__game_id")

    class Meta:
        model = LLMCall
        fields = []
