from django.urls import path

from . import views

urlpatterns = [
    path("game/<str:game_id>/available-bots/", views.AvailableBotListView.as_view(), name="game-available-bots"),
    path("game/<str:game_id>/add-bot/", views.BotMemberCreateView.as_view(), name="game-add-bot"),
]
