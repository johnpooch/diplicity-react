from django.urls import path
from .views import (
    ChannelCreateView,
    ChannelMessageCreateView,
    ChannelListView,
)

urlpatterns = [
    path("games/<str:game_id>/channels/", ChannelListView.as_view(), name="channel-list"),
    path("games/<str:game_id>/channels/create/", ChannelCreateView.as_view(), name="channel-create"),
    path(
        "games/<str:game_id>/channels/<int:channel_id>/messages/create/",
        ChannelMessageCreateView.as_view(),
        name="channel-message-create",
    ),
]
