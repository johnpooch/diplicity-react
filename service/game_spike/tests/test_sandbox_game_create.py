import pytest
from django.urls import reverse

from common.constants import GameStatus
from game_spike.factories import UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:sandbox-game-create")


class TestSandboxGameCreate:
    def test_creator_plays_every_nation_in_started_sandbox(self, authenticated_client_factory):
        user = UserFactory()
        response = authenticated_client_factory(user).post(
            URL, {"name": "Practice", "variant_id": "classical"}, format="json"
        )
        assert response.status_code == 201
        assert response.data["status"] == GameStatus.ACTIVE
        assert response.data["sandbox"] is True
        assert {member["user_id"] for member in response.data["members"]} == {user.id}
        assert len(response.data["members"]) == 7

    def test_sandbox_start_sends_no_notification(self, authenticated_client_factory, assert_notification):
        user = UserFactory()
        authenticated_client_factory(user).post(URL, {"name": "Practice", "variant_id": "classical"}, format="json")
        assert_notification(user, "game_start", sent=False)

    def test_unknown_variant_is_rejected(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(
            URL, {"name": "Practice", "variant_id": "nope"}, format="json"
        )
        assert response.status_code == 400
        assert "variant_id" in response.data

    def test_name_is_required(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(URL, {"variant_id": "classical"}, format="json")
        assert response.status_code == 400
        assert "name" in response.data

    def test_unauthenticated_user_cannot_create_sandbox(self, unauthenticated_client):
        response = unauthenticated_client.post(URL, {"name": "Practice", "variant_id": "classical"}, format="json")
        assert response.status_code == 401
