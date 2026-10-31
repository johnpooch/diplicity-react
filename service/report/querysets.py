from django.db import models

from .constants import ReportDecision
from .policies import ModeratorPolicy


class ReportQuerySet(models.QuerySet):
    def visible_to(self, actor):
        if ModeratorPolicy.decide(None, actor):
            return self
        if not actor.is_authenticated:
            return self.none()
        return self.filter(reporter__user_id=actor.pk)

    def pending(self):
        return self.filter(review__isnull=True)

    def approved(self):
        return self.filter(review__decision=ReportDecision.APPROVED)

    def rejected(self):
        return self.filter(review__decision=ReportDecision.REJECTED)
