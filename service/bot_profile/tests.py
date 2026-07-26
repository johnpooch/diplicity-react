import pytest
from django.urls import reverse
from rest_framework import status

from bot_profile.models import BotProfile
from bot_profile.utils import get_bot_user
from common.constants import GameStatus, PhaseStatus
from game.models import Game

game_create_viewname = "game-create"
available_bots_viewname = "game-available-bots"
add_bot_viewname = "game-add-bot"


def _create_game_via_api(client, variant_id, **overrides):
    payload = {
        "name": "Bot Seat Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    response = client.post(reverse(game_create_viewname), payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    return Game.objects.get(id=response.data["id"])


def _first_roster_bot_user():
    return (
        BotProfile.objects.exclude(user=get_bot_user())
        .order_by("user__profile__name")
        .first()
        .user
    )


class TestBotRoster:

    @pytest.mark.django_db
    def test_roster_is_seeded(self):
        roster = BotProfile.objects.exclude(user=get_bot_user())
        assert roster.count() == 12
        assert all(profile.disposition and profile.voice for profile in roster)

    @pytest.mark.django_db
    def test_bot_user_has_profile(self):
        assert BotProfile.objects.filter(user=get_bot_user()).exists()


class TestGetBotUser:

    @pytest.mark.django_db
    def test_get_bot_user_ignores_email(self):
        bot_user = get_bot_user()
        bot_user.email = "not-the-magic-email@example.com"
        bot_user.save()

        assert get_bot_user() == bot_user


class TestAvailableBots:

    @pytest.mark.django_db
    def test_lists_roster_sorted_by_name(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 12
        names = [bot["name"] for bot in response.data]
        assert names == sorted(names)
        assert all(bot["user_id"] for bot in response.data)
        assert get_bot_user().id not in [bot["user_id"] for bot in response.data]

    @pytest.mark.django_db
    def test_excludes_bots_already_in_game(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        game.members.create(user=bot_user)

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 11
        assert bot_user.id not in [bot["user_id"] for bot in response.data]

    @pytest.mark.django_db
    def test_non_admin_forbidden(
        self, authenticated_client, authenticated_client_for_secondary_user, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com", "secondary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client_for_secondary_user.get(
            reverse(available_bots_viewname, args=[game.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_not_allowlisted_forbidden(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.get(reverse(available_bots_viewname, args=[game.id]))

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_non_pending_game_forbidden(self, authenticated_client, active_game_created_by_primary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]

        response = authenticated_client.get(
            reverse(available_bots_viewname, args=[active_game_created_by_primary_user.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddBot:

    @pytest.mark.django_db
    def test_admin_adds_roster_bot(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_bot"] is True
        assert response.data["name"] == bot_user.profile.name
        bot_member = game.members.get(user=bot_user)
        public_channel = game.channels.get(private=False)
        assert public_channel.member_channels.filter(member=bot_member).exists()
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING

    @pytest.mark.django_db
    def test_filling_last_seat_starts_game(self, authenticated_client, italy_vs_germany_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, italy_vs_germany_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE
        assert game.current_phase.status == PhaseStatus.ACTIVE

    @pytest.mark.django_db
    def test_game_master_adds_roster_bot(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(
            authenticated_client, classical_variant.id, private=True, game_master=True
        )
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert game.members.filter(user=bot_user).exists()

    @pytest.mark.django_db
    def test_bot_already_in_game_rejected(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        game.members.create(user=bot_user)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_generic_bot_rejected(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": get_bot_user().id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_human_user_rejected(self, authenticated_client, classical_variant, secondary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": secondary_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_non_admin_forbidden(
        self, authenticated_client, authenticated_client_for_secondary_user, classical_variant, settings
    ):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com", "secondary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()

        response = authenticated_client_for_secondary_user.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_not_allowlisted_forbidden(self, authenticated_client, classical_variant, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        game = _create_game_via_api(authenticated_client, classical_variant.id)
        bot_user = _first_roster_bot_user()
        settings.BOT_OPPONENT_ALLOWLIST = []

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[game.id]), {"user_id": bot_user.id}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_non_pending_game_forbidden(self, authenticated_client, active_game_created_by_primary_user, settings):
        settings.BOT_OPPONENT_ALLOWLIST = ["primary@example.com"]
        bot_user = _first_roster_bot_user()

        response = authenticated_client.post(
            reverse(add_bot_viewname, args=[active_game_created_by_primary_user.id]),
            {"user_id": bot_user.id},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
