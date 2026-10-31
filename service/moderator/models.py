from report.models import Report

from .managers import ModerationReportManager


class ModerationReport(Report):
    objects = ModerationReportManager()

    class Meta:
        proxy = True
