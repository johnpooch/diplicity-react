from django.urls import path

from . import views

urlpatterns = [
    path(
        "report/reasons/",
        views.ReportReasonListView.as_view(),
        name="report-reason-list",
    ),
    path(
        "game/<str:game_id>/member/<int:member_id>/report/",
        views.ReportCreateView.as_view(),
        name="game-member-report",
    ),
]
