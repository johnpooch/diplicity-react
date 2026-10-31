from django.db.models import Manager

from .querysets import ModerationReportQuerySet


class ModerationReportManager(Manager.from_queryset(ModerationReportQuerySet)):
    pass
