from django.urls import path
from .views import (
    ChannelCreateView,
    ChannelMessageCreateView,
    ChannelMessageListView,
    ChannelMarkReadView,
    ChannelMuteView,
    ChannelPreviewListView,
    ChannelRetrieveUpdateView,
)

urlpatterns = [
    path(
        "games/<str:game_id>/channel-previews/",
        ChannelPreviewListView.as_view(),
        name="channel-preview-list",
    ),
    path(
        "games/<str:game_id>/channels/create/",
        ChannelCreateView.as_view(),
        name="channel-create",
    ),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/",
        ChannelRetrieveUpdateView.as_view(),
        name="channel-update",
    ),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/messages/",
        ChannelMessageListView.as_view(),
        name="channel-message-list",
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
    path(
        "games/<str:game_id>/channels/<int:channel_id>/mute/",
        ChannelMuteView.as_view(),
        name="channel-mute",
    ),
]
