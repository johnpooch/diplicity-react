from django.db import models
from django.db.models import F, Value, Window
from django.db.models.functions import Extract, Rank

from .calculation import DEFAULT_PARAMETERS


class RatingQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self

    def established(self, now, parameters=DEFAULT_PARAMETERS):
        growth_per_second = (
            parameters.volatility**2 / parameters.period.total_seconds()
        )
        return self.alias(
            grown_variance=F("deviation") * F("deviation")
            + Value(growth_per_second)
            * (Value(now.timestamp()) - Extract("rated_at", "epoch"))
        ).filter(grown_variance__lte=parameters.ranked_deviation**2)

    def ranked(self):
        return self.annotate(
            rank=Window(Rank(), order_by=F("rating").desc())
        ).order_by("-rating", "user_id")

    def rank_of(self, rating):
        return self.filter(rating__gt=rating.rating).count() + 1


class RatingResultQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self


class RatingPairingQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self
