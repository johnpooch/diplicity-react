import pytest
from django.urls import reverse

from common.constants import DeniedReason
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-pause", args=[game_id])


class TestGamePause:
    def test_manager_can_pause_active_game(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert response.status_code == 200
        assert response.data["is_paused"] is True

    def test_pausing_notifies_players_but_not_the_manager(self, authenticated_client_factory, assert_notification):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert_notification(player, "game_paused")
        assert_notification(game.created_by, "game_paused", sent=False)

    def test_player_cannot_pause_game(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        response = authenticated_client_factory(player).patch(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_GAME_MANAGER

    def test_cannot_pause_paused_game(self, authenticated_client_factory):
        game = GameFactory(paused=True)
        response = authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_PAUSED

    def test_cannot_pause_pending_game(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_NOT_ACTIVE

    def test_refused_pause_sends_no_notification(self, authenticated_client_factory, assert_notification):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        authenticated_client_factory(player).patch(_url(game.id))
        assert_notification(game.created_by, "game_paused", sent=False)

    def test_unauthenticated_user_cannot_pause_game(self, unauthenticated_client):
        game = GameFactory(active=True)
        response = unauthenticated_client.patch(_url(game.id))
        assert response.status_code == 401

    def test_pausing_missing_game_returns_404(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).patch(_url("missing-game"))
        assert response.status_code == 404
