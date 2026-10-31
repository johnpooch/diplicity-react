from django_filters import rest_framework as filters

from .constants import ReportStatus
from .models import Report

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
        model = Report
        fields = ()

    def filter_status(self, queryset, name, value):
        return getattr(queryset, value)().order_by(STATUS_ORDERING[value])
