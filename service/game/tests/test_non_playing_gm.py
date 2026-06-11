import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from common.constants import DeadlineMode, MovementPhaseDuration
from game import models
from user_profile.models import UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def game_with_non_playing_gm(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(gm_user=None):
        if gm_user is None:
            gm_user = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Non-playing GM Game",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
        )
        game.members.create(user=gm_user, is_game_master=True)

        for i in range(game.variant.nations.count()):
            other_user = User.objects.create_user(f"npm_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"NPM Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game
    return _create


class TestNonPlayingGMStart:
    def test_non_playing_gm_has_no_nation_after_start(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        gm_member = game.members.get(user=primary_user)
        assert gm_member.nation is None

    def test_non_playing_gm_has_no_phase_state(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        gm_member = game.members.get(user=primary_user)
        assert not gm_member.phase_states.exists()

    def test_all_playing_members_get_nations(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        playing_members = game.members.exclude(user=primary_user)
        for member in playing_members:
            assert member.nation is not None

    def test_playing_gm_still_gets_nation(self, db, primary_user, classical_variant, adjudication_data_classical):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Playing GM Game",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=False,
        )
        game.members.create(user=primary_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"pgm_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"PGM Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        gm_member = game.members.get(user=primary_user)
        assert gm_member.nation is not None


class TestNonPlayingGMCreateEndpoint:
    def test_create_game_with_non_playing_gm(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "NPM Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": True,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
                "nonPlayingGm": True,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["non_playing_gm"] is True

    def test_create_game_with_non_playing_gm_requires_private(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "NPM Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": False,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
                "nonPlayingGm": True,
            },
            format="json",
        )
        assert response.status_code == 400

    def test_create_game_without_non_playing_gm_defaults_false(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "Normal Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": False,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["non_playing_gm"] is False


class TestNonPlayingGMMemberName:
    def test_non_playing_gm_name_is_game_master(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        api_client.force_authenticate(user=primary_user)
        response = api_client.get(f"/game/{game.id}/")
        assert response.status_code == 200
        gm_member = next(m for m in response.data["members"] if m["is_game_master"])
        assert gm_member["name"] == "Game Master"

    def test_playing_gm_name_is_real_name(self, db, primary_user, classical_variant, adjudication_data_classical, api_client):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Playing GM Name Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=False,
        )
        game.members.create(user=primary_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"pgmn_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"PGMN Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        api_client.force_authenticate(user=primary_user)
        response = api_client.get(f"/game/{game.id}/")
        assert response.status_code == 200
        gm_member = next(m for m in response.data["members"] if m["is_game_master"])
        assert gm_member["name"] == primary_user.profile.name


class TestNonPlayingGMLeave:
    def test_gm_leaving_promotes_first_player_as_playing_gm(self, db, primary_user, classical_variant, api_client):
        second_user = User.objects.create_user("second@test.com", password="testpass")
        UserProfile.objects.create(user=second_user, name="Second Player")
        third_user = User.objects.create_user("third@test.com", password="testpass")
        UserProfile.objects.create(user=third_user, name="Third Player")

        game = models.Game.objects.create_from_template(
            classical_variant,
            name="GM Leave Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)
        second_member = game.members.create(user=second_user)
        game.members.create(user=third_user)

        api_client.force_authenticate(user=primary_user)
        response = api_client.delete(f"/game/{game.id}/leave/")
        assert response.status_code == 204

        game.refresh_from_db()
        assert game.non_playing_gm is False
        second_member.refresh_from_db()
        assert second_member.is_game_master is True
        assert not game.members.filter(user=primary_user).exists()

    def test_gm_leaving_with_no_other_players_deletes_game(self, db, primary_user, classical_variant, api_client):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="GM Leave Solo Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)

        api_client.force_authenticate(user=primary_user)
        response = api_client.delete(f"/game/{game.id}/leave/")
        assert response.status_code == 204

        from game.models import Game
        assert not Game.objects.filter(id=game.id).exists()
