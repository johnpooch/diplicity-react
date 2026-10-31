from common.loaders import Loader

from .models import Report


class ReportLoader(Loader):
    queryset = Report.objects.select_related("review")


class ModerationReportLoader(Loader):
    queryset = Report.objects.select_related(
        "review__reviewed_by__profile",
        "reporter__game__variant",
        "reporter__nation",
        "reporter__user__profile",
        "reported__nation",
        "reported__user__profile",
    )
