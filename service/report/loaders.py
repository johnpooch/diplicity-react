from common.loaders import Loader

from .models import Report


class ReportLoader(Loader):
    queryset = Report.objects.select_related("review")
