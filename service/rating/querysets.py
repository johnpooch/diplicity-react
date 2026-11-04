from django.db import models
from django.db.models import (
    Case,
    Count,
    DurationField,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Extract, Greatest

from .calculation import DEFAULT_PARAMETERS


def _grown_variance(now, parameters):
    idle_seconds = Greatest(
        Extract(
            ExpressionWrapper(Value(now) - F("rated_at"), output_field=DurationField()),
            "epoch",
        ),
        Value(0),
    )
    return ExpressionWrapper(
        F("deviation") * F("deviation")
        + idle_seconds
        * Value(parameters.volatility**2 / parameters.period.total_seconds()),
        output_field=FloatField(),
    )


class RatingQuerySet(models.QuerySet):
    def established(self, now, parameters=DEFAULT_PARAMETERS):
        return self.alias(grown_variance=_grown_variance(now, parameters)).filter(
            grown_variance__lte=parameters.ranked_deviation**2
        )

    def with_rank(self, now, parameters=DEFAULT_PARAMETERS):
        higher = (
            self.model.objects.established(now, parameters)
            .filter(rating__gt=OuterRef("rating"))
            .order_by()
            .annotate(
                count=Func(F("pk"), function="COUNT", output_field=IntegerField())
            )
            .values("count")
        )
        return self.alias(grown_variance=_grown_variance(now, parameters)).annotate(
            rank=Case(
                When(
                    grown_variance__lte=parameters.ranked_deviation**2,
                    then=Subquery(higher) + 1,
                ),
                default=None,
                output_field=IntegerField(),
            )
        )

    def with_record(self):
        rated = Q(user__members__rating_result__isnull=False)
        return self.annotate(
            won=Count("user__members", filter=rated & Q(user__members__won=True)),
            drew=Count("user__members", filter=rated & Q(user__members__drew=True)),
            lost=Count(
                "user__members",
                filter=rated
                & Q(user__members__won=False, user__members__drew=False),
            ),
        )


class RatingResultQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self


class RatingPairingQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self
