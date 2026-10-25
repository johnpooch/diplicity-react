import pytest
from django.urls import reverse

from common.constants import DeniedReason, GameStatus
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-clone-to-sandbox", args=[game_id])


class TestGameCloneToSandbox:
    def test_player_can_clone_active_game_into_sandbox(self, authenticated_client_factory):
        game = GameFactory(active=True, name="Big War")
        response = authenticated_client_factory(game.created_by).post(_url(game.id))
        assert response.status_code == 201
        assert response.data["sandbox"] is True
        assert response.data["status"] == GameStatus.ACTIVE
        assert response.data["name"] == "Big War (Sandbox)"

    def test_fourth_sandbox_replaces_the_oldest(self, authenticated_client_factory):
        game = GameFactory(active=True)
        client = authenticated_client_factory(game.created_by)
        oldest = client.post(_url(game.id)).data["id"]
        client.post(_url(game.id))
        client.post(_url(game.id))
        client.post(_url(game.id))
        assert client.get(reverse("game_spike:game-retrieve", args=[oldest])).status_code == 404

    def test_outsider_cannot_clone_game(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(UserFactory()).post(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_PLAYER

    def test_cannot_clone_pending_game(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(game.created_by).post(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_NOT_ACTIVE

    def test_cannot_clone_sandbox_game(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True)
        response = authenticated_client_factory(game.created_by).post(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.SANDBOX_GAME

    def test_unauthenticated_user_cannot_clone_game(self, unauthenticated_client):
        game = GameFactory(active=True)
        response = unauthenticated_client.post(_url(game.id))
        assert response.status_code == 401

    def test_cloning_missing_game_returns_404(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).post(_url("missing-game"))
        assert response.status_code == 404
