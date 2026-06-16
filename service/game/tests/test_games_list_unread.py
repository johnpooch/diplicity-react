import pytest
from django.urls import reverse
from rest_framework import status

from channel.models import Channel, ChannelMessage


def _find_game(response, game_id):
    results = response.data.get("results", response.data)
    return next(g for g in results if g["id"] == game_id)


class TestGamesListUnreadCount:

    @pytest.mark.django_db
    def test_games_list_includes_total_unread_count(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        response = authenticated_client.get(reverse("game-list") + "?mine=1")

        assert response.status_code == status.HTTP_200_OK
        assert _find_game(response, game.id)["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_games_list_unread_count_zero_for_anonymous(
        self, unauthenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        response = unauthenticated_client.get(reverse("game-list"))

        assert response.status_code == status.HTTP_200_OK
        assert _find_game(response, game.id)["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_own_messages_not_counted_in_list_unread(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        primary_member = game.members.first()
        channel = Channel.objects.get(game=game, name="Public Press")
        ChannelMessage.objects.create(channel=channel, sender=primary_member, body="Own message")

        response = authenticated_client.get(reverse("game-list") + "?mine=1")

        assert response.status_code == status.HTTP_200_OK
        assert _find_game(response, game.id)["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_games_list_unread_count_resets_after_mark_read(
        self, authenticated_client, game_with_public_channel_and_messages
    ):
        game = game_with_public_channel_and_messages
        channel = Channel.objects.get(game=game, name="Public Press")

        authenticated_client.post(reverse("channel-mark-read", args=[game.id, channel.id]))

        response = authenticated_client.get(reverse("game-list") + "?mine=1")

        assert response.status_code == status.HTTP_200_OK
        assert _find_game(response, game.id)["total_unread_message_count"] == 0
