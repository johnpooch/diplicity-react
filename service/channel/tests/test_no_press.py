import pytest
from django.apps import apps
from django.urls import reverse
from rest_framework import status
from channel.models import Channel

from common.constants import GameStatus, PressType


@pytest.fixture
def no_press_active_game(db, primary_user, classical_variant, classical_england_nation):
    Game = apps.get_model("game", "Game")
    game = Game.objects.create(
        name="No Press Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
        press_type=PressType.NO_PRESS,
    )
    game.members.create(user=primary_user, nation=classical_england_nation)
    return game


@pytest.fixture
def no_press_active_game_with_channel(no_press_active_game):
    channel = Channel.objects.create(game=no_press_active_game, name="Public Press", private=False)
    channel.members.add(no_press_active_game.members.first())
    return no_press_active_game


@pytest.fixture
def no_press_completed_game(db, primary_user, classical_variant, classical_england_nation):
    Game = apps.get_model("game", "Game")
    game = Game.objects.create(
        name="No Press Completed Game",
        variant=classical_variant,
        status=GameStatus.COMPLETED,
        press_type=PressType.NO_PRESS,
    )
    game.members.create(user=primary_user, nation=classical_england_nation)
    return game


@pytest.fixture
def no_press_completed_game_with_channel(no_press_completed_game, secondary_user, classical_france_nation):
    game = no_press_completed_game
    game.members.create(user=secondary_user, nation=classical_france_nation)
    channel = Channel.objects.create(game=game, name="Public Press", private=False)
    channel.members.add(game.members.first())
    return game


class TestNoPressChannelCreate:

    @pytest.mark.django_db
    def test_active_no_press_game_blocks_channel_creation(
        self, authenticated_client, no_press_active_game
    ):
        url = reverse("channel-create", args=[no_press_active_game.id])
        payload = {"member_ids": []}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_completed_no_press_game_allows_channel_creation(
        self, authenticated_client, no_press_completed_game, secondary_user, classical_france_nation
    ):
        other_member = no_press_completed_game.members.create(
            user=secondary_user, nation=classical_france_nation
        )
        url = reverse("channel-create", args=[no_press_completed_game.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_full_press_active_game_allows_channel_creation(
        self, authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
    ):
        other_member = active_game_with_phase_state.members.create(
            user=secondary_user, nation=classical_france_nation
        )
        url = reverse("channel-create", args=[active_game_with_phase_state.id])
        payload = {"member_ids": [other_member.id]}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestNoPressChannelMessageCreate:

    @pytest.mark.django_db
    def test_active_no_press_game_blocks_message_sending(
        self, authenticated_client, no_press_active_game_with_channel
    ):
        channel = Channel.objects.get(game=no_press_active_game_with_channel)
        url = reverse(
            "channel-message-create",
            args=[no_press_active_game_with_channel.id, channel.id],
        )
        payload = {"body": "This should be blocked"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_completed_no_press_game_allows_message_sending(
        self,
        authenticated_client,
        no_press_completed_game_with_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        channel = Channel.objects.get(game=no_press_completed_game_with_channel)
        url = reverse(
            "channel-message-create",
            args=[no_press_completed_game_with_channel.id, channel.id],
        )
        payload = {"body": "Debriefing after the game!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_full_press_game_allows_message_sending(
        self,
        authenticated_client,
        active_game_with_private_channel,
        mock_send_notification_to_users,
        mock_immediate_on_commit,
    ):
        channel = Channel.objects.get(game=active_game_with_private_channel, private=True)
        url = reverse(
            "channel-message-create",
            args=[active_game_with_private_channel.id, channel.id],
        )
        payload = {"body": "Hello, world!"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestNoPressChannelList:

    @pytest.mark.django_db
    def test_active_no_press_game_allows_channel_list(
        self, authenticated_client, no_press_active_game_with_channel
    ):
        url = reverse("channel-list", args=[no_press_active_game_with_channel.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
