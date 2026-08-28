from django.urls import path

from . import views

urlpatterns = [
    path("game/<str:game_id>/member/", views.MemberCreateView.as_view(), name="game-member-create"),
    path("game/<str:game_id>/member/join/", views.MemberJoinView.as_view(), name="game-join"),
    path("game/<str:game_id>/leave/", views.MemberDeleteView.as_view(), name="game-leave"),
    path("game/<str:game_id>/kick/<int:member_id>/", views.MemberKickView.as_view(), name="game-kick"),
    path("game/<str:game_id>/members/<int:member_id>/replace/", views.MemberReplaceView.as_view(), name="game-member-replace"),
    path("game/<str:game_id>/recover-from-civil-disorder/", views.CivilDisorderRecoveryView.as_view(), name="civil-disorder-recovery"),
    path("game/<str:game_id>/member/nation-preference/", views.MemberNationPreferenceView.as_view(), name="game-member-nation-preference"),
    path("game/<str:game_id>/member/<int:member_id>/nation/", views.MemberNationAssignView.as_view(), name="game-member-nation-assign"),
    path("game/<str:game_id>/join/", views.LegacyMemberJoinView.as_view(), name="game-join-legacy"),
    path("game/<str:game_id>/add-bot/", views.LegacyMemberCreateView.as_view(), name="game-add-bot-legacy"),
]