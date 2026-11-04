from django.db import models


class RatingResultQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self


class RatingPairingQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self
