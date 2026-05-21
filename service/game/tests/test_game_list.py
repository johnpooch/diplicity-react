import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from game.models import Game
from channel.models import Channel, ChannelMember, ChannelMessage

game_list_viewname = "game-list"


def create_game_with_member(classical_variant, user):
    game = Game.objects.create(
        name="Test Game",
        variant=classical_variant,
        status="active",
    )
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status="active",
        ordinal=1,
    )
    member = game.members.create(user=user)
    return game, member


class TestGameListUnreadCount:

    @pytest.mark.django_db
    def test_returns_zero_when_no_messages(
        self, authenticated_client, primary_user, classical_variant
    ):
        create_game_with_member(classical_variant, primary_user)
        url = reverse(game_list_viewname)
        response = authenticated_client.get(url, {"mine": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_returns_count_of_unread_messages(
        self, authenticated_client, primary_user, classical_variant
    ):
        game, member = create_game_with_member(classical_variant, primary_user)
        channel = Channel.objects.create(game=game, name="Public", private=False)
        channel_member = ChannelMember.objects.create(
            member=member,
            channel=channel,
            last_read_at=timezone.now() - timezone.timedelta(hours=1),
        )
        ChannelMessage.objects.create(channel=channel, sender=member, body="Hello")
        ChannelMessage.objects.create(channel=channel, sender=member, body="World")

        url = reverse(game_list_viewname)
        response = authenticated_client.get(url, {"mine": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["total_unread_message_count"] == 2

    @pytest.mark.django_db
    def test_returns_zero_for_unauthenticated_user(
        self, unauthenticated_client, primary_user, classical_variant
    ):
        game, member = create_game_with_member(classical_variant, primary_user)
        game.private = False
        game.save()
        channel = Channel.objects.create(game=game, name="Public", private=False)
        ChannelMessage.objects.create(channel=channel, sender=member, body="Hello")

        url = reverse(game_list_viewname)
        response = unauthenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["total_unread_message_count"] == 0

    @pytest.mark.django_db
    def test_does_not_count_messages_before_last_read_at(
        self, authenticated_client, primary_user, classical_variant
    ):
        game, member = create_game_with_member(classical_variant, primary_user)
        channel = Channel.objects.create(game=game, name="Public", private=False)
        ChannelMessage.objects.create(channel=channel, sender=member, body="Old message")
        ChannelMember.objects.create(
            member=member,
            channel=channel,
            last_read_at=timezone.now(),
        )

        url = reverse(game_list_viewname)
        response = authenticated_client.get(url, {"mine": "true"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["total_unread_message_count"] == 0
