from django.db.models import BooleanField, Case, Value, When, Prefetch
from django.shortcuts import get_object_or_404

from .. import models
from .base_service import BaseService


class GameService(BaseService):
    def __init__(self, user):
        self.user = user

    def list(self, filters=None):
        filters = filters or {}
        if filters.get("mine"):
            queryset = models.Game.objects.filter(members__user=self.user).distinct()
        elif filters.get("can_join"):
            queryset = (
                models.Game.objects.filter(status=models.Game.PENDING)
                .exclude(members__user=self.user)
                .distinct()
            )
        else:
            queryset = models.Game.objects.all()

        queryset = queryset.prefetch_related(
            Prefetch(
                "members",
                queryset=models.Member.objects.annotate(
                    is_current_user=Case(
                        When(user=self.user, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                ),
            )
        ).annotate(
            can_join=Case(
                When(
                    status=models.Game.PENDING,
                    members__user=self.user,
                    then=Value(False),
                ),
                default=Value(True),
                output_field=BooleanField(),
            ),
            can_leave=Case(
                When(
                    status=models.Game.PENDING,
                    members__user=self.user,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )

        return queryset

    def retrieve(self, game_id):
        queryset = models.Game.objects.prefetch_related(
            Prefetch(
                "members",
                queryset=models.Member.objects.annotate(
                    is_current_user=Case(
                        When(user=self.user, then=Value(True)),
                        default=Value(False),
                        output_field=BooleanField(),
                    )
                ),
            )
        ).annotate(
            can_join=Case(
                When(
                    status=models.Game.PENDING,
                    members__user=self.user,
                    then=Value(False),
                ),
                default=Value(True),
                output_field=BooleanField(),
            ),
            can_leave=Case(
                When(
                    status=models.Game.PENDING,
                    members__user=self.user,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
        return get_object_or_404(queryset, id=game_id)
