import pytest
from django.urls import reverse
from rest_framework import status

from bot.utils import get_bot_user
from game.models import Game


create_viewname = "game-create"


def bot_payload(variant_id, include_bot_opponent):
    return {
        "name": "Bot Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
        "include_bot_opponent": include_bot_opponent,
    }


class TestBotOpponentSeating:

    @pytest.mark.django_db
    def test_allowed_user_seats_bot_opponent(
        self, authenticated_client, italy_vs_germany_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, bot_payload(italy_vs_germany_variant.id, True), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.members.count() == 2
        assert game.members.filter(user=get_bot_user()).exists()

    @pytest.mark.django_db
    def test_bot_opponent_added_to_public_channel(
        self, authenticated_client, italy_vs_germany_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, bot_payload(italy_vs_germany_variant.id, True), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        bot_member = game.members.get(user=get_bot_user())
        public_channel = game.channels.get(private=False)
        assert public_channel.member_channels.filter(member=bot_member).exists()

    @pytest.mark.django_db
    def test_disallowed_user_cannot_seat_bot_opponent(
        self, authenticated_client, italy_vs_germany_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = []
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, bot_payload(italy_vs_germany_variant.id, True), format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_no_bot_opponent_by_default(
        self, authenticated_client, italy_vs_germany_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, bot_payload(italy_vs_germany_variant.id, False), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.members.count() == 1
        assert not game.members.filter(user=get_bot_user()).exists()


class TestCanCreateBotGamesFlag:

    @pytest.mark.django_db
    def test_profile_reports_allowed_user(self, authenticated_client, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        response = authenticated_client.get(reverse("user-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_create_bot_games"] is True

    @pytest.mark.django_db
    def test_profile_reports_disallowed_user(self, authenticated_client, settings):
        settings.BOT_OPPONENT_ALLOWLIST = []
        response = authenticated_client.get(reverse("user-profile"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_create_bot_games"] is False
