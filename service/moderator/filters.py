from django_filters import rest_framework as filters

from report.constants import ReportStatus

from .models import ModerationReport

STATUS_ORDERING = {
    ReportStatus.PENDING: "created_at",
    ReportStatus.APPROVED: "-created_at",
    ReportStatus.REJECTED: "-created_at",
}


class ModerationReportFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=ReportStatus.STATUS_CHOICES, method="filter_status", required=True
    )

    class Meta:
        model = ModerationReport
        fields = ()

    def filter_status(self, queryset, name, value):
        return getattr(queryset, value)().order_by(STATUS_ORDERING[value])
