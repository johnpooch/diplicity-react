from django.urls import path

from . import views

urlpatterns = [
    path(
        "moderation/reports/",
        views.ModerationReportListView.as_view(),
        name="moderation-report-list",
    ),
    path(
        "moderation/reports/<int:pk>/",
        views.ModerationReportDetailView.as_view(),
        name="moderation-report-detail",
    ),
]
