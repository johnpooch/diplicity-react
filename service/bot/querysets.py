from django.db import models
from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone

from phase.models import Phase

from .constants import RunStatus


class RunQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self

    def pending(self):
        return self.filter(status=RunStatus.PENDING)

    def running(self):
        return self.filter(status=RunStatus.RUNNING)

    def ready(self):
        return self.pending().filter(earliest_start_at__lte=timezone.now())

    def stale_phase(self):
        current_phase = Phase.objects.filter(game=OuterRef("phase__game")).order_by(
            "-ordinal", "-id"
        )
        return self.pending().exclude(phase=Subquery(current_phase.values("pk")[:1]))

    def overdue(self, steps):
        now = timezone.now()
        condition = Q(pk__in=[])
        for name, step in steps.items():
            condition |= Q(step=name, started_at__lt=now - step.timeout)
        return self.running().filter(condition)
