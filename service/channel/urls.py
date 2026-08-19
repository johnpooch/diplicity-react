from django.urls import path
from .views import (
    ChannelCreateView,
    ChannelMessageCreateView,
    ChannelListView,
    ChannelMarkReadView,
    ChannelRetrieveView,
    ChannelUnreadRetrieveView,
    GameUnreadListView,
)

urlpatterns = [
    path("game/unread/", GameUnreadListView.as_view(), name="game-unread-list"),
    path(
        "game/<str:game_id>/channel/unread/",
        ChannelUnreadRetrieveView.as_view(),
        name="game-channel-unread",
    ),
    path("games/<str:game_id>/channels/", ChannelListView.as_view(), name="channel-list"),
    path("games/<str:game_id>/channels/create/", ChannelCreateView.as_view(), name="channel-create"),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/",
        ChannelRetrieveView.as_view(),
        name="channel-retrieve",
    ),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/messages/create/",
        ChannelMessageCreateView.as_view(),
        name="channel-message-create",
    ),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/mark-read/",
        ChannelMarkReadView.as_view(),
        name="channel-mark-read",
    ),
]
