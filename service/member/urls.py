from django.urls import path

from . import views

urlpatterns = [
    path("game/<str:game_id>/join/", views.MemberCreateView.as_view(), name="game-join"),
    path("game/<str:game_id>/leave/", views.MemberDeleteView.as_view(), name="game-leave"),
    path("game/<str:game_id>/kick/<int:member_id>/", views.MemberKickView.as_view(), name="game-kick"),
    path("game/<str:game_id>/members/<int:member_id>/replace/", views.MemberReplaceView.as_view(), name="game-member-replace"),
    path("game/<str:game_id>/recover-from-civil-disorder/", views.CivilDisorderRecoveryView.as_view(), name="civil-disorder-recovery"),
]