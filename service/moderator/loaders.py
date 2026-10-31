from common.loaders import Loader

from .models import ModerationReport


class ModerationReportLoader(Loader):
    queryset = ModerationReport.objects.select_related(
        "review",
        "reporter__game__variant",
        "reporter__nation",
        "reporter__user__profile",
        "reported__nation",
        "reported__user__profile",
    )
