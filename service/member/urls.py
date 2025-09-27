from django.urls import path

from . import views

urlpatterns = [
    path("game/<str:game_id>/join/", views.MemberCreateView.as_view(), name="game-join"),
    path("game/<str:game_id>/leave/", views.MemberDeleteView.as_view(), name="game-leave"),
]