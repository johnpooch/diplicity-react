import pytest
from django.urls import reverse

from common.constants import Commitment, CommitmentRequirement, DeadlineMode, GameStatus, MovementPhaseDuration
from game_spike.factories import UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:game-create")


def _payload(**overrides):
    payload = {
        "name": "Spring Offensive",
        "variant_id": "classical",
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
        "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS,
    }
    payload.update(overrides)
    return payload


class TestGameCreate:
    def test_creator_is_seated_in_new_pending_game(self, authenticated_client_factory):
        user = UserFactory()
        response = authenticated_client_factory(user).post(URL, _payload(), format="json")
        assert response.status_code == 201
        assert response.data["status"] == GameStatus.PENDING
        assert [member["user_id"] for member in response.data["members"]] == [user.id]
        assert response.data["can_manage"] is True

    def test_game_id_is_a_slug_of_the_name(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(URL, _payload(), format="json")
        assert response.data["id"].startswith("spring-offensive-")

    def test_creator_can_run_private_game_as_game_master(self, authenticated_client_factory):
        user = UserFactory()
        response = authenticated_client_factory(user).post(URL, _payload(private=True, game_master=True), format="json")
        assert response.status_code == 201
        assert response.data["members"] == []
        assert response.data["game_master"]["user_id"] == user.id

    def test_game_master_requires_private_game(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(URL, _payload(game_master=True), format="json")
        assert response.status_code == 400
        assert "game_master" in response.data

    def test_low_commitment_user_cannot_create_public_game(self, authenticated_client_factory):
        user = UserFactory(profile__commitment=Commitment.LOW)
        response = authenticated_client_factory(user).post(URL, _payload(), format="json")
        assert response.status_code == 400
        assert "commitment_requirement" in response.data

    def test_low_commitment_user_can_create_private_game(self, authenticated_client_factory):
        user = UserFactory(profile__commitment=Commitment.LOW)
        response = authenticated_client_factory(user).post(URL, _payload(private=True), format="json")
        assert response.status_code == 201

    def test_only_high_commitment_user_can_require_committed_players(self, authenticated_client_factory):
        user = UserFactory(profile__commitment=Commitment.MEDIUM)
        response = authenticated_client_factory(user).post(
            URL, _payload(commitment_requirement=CommitmentRequirement.COMMITTED), format="json"
        )
        assert response.status_code == 400

    def test_fixed_time_game_requires_deadline_settings(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(
            URL, _payload(deadline_mode=DeadlineMode.FIXED_TIME), format="json"
        )
        assert response.status_code == 400
        assert "fixed_deadline_time" in response.data

    def test_short_phases_require_private_game(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(
            URL, _payload(movement_phase_duration=MovementPhaseDuration.FIVE_MINUTES), format="json"
        )
        assert response.status_code == 400
        assert "movement_phase_duration" in response.data

    def test_unknown_timezone_is_rejected(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(
            URL, _payload(fixed_deadline_timezone="Mars/Olympus"), format="json"
        )
        assert response.status_code == 400
        assert "fixed_deadline_timezone" in response.data

    def test_unknown_variant_is_rejected(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(URL, _payload(variant_id="nope"), format="json")
        assert response.status_code == 400
        assert "variant_id" in response.data

    def test_unauthenticated_user_cannot_create_game(self, unauthenticated_client):
        response = unauthenticated_client.post(URL, _payload(), format="json")
        assert response.status_code == 401
