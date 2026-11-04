from django.urls import path

from . import views

urlpatterns = [
    path("leaderboard/", views.LeaderboardListView.as_view(), name="leaderboard"),
]
