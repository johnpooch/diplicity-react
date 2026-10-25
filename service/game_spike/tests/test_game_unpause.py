import pytest
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from common.constants import DeniedReason
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-unpause", args=[game_id])


def _deadline(client, game):
    response = client.get(reverse("game_spike:game-list"), {"mine": "true"})
    return parse_datetime(response.data["results"][0]["current_phase"]["scheduled_resolution"])


class TestGameUnpause:
    def test_manager_can_unpause_paused_game(self, authenticated_client_factory):
        game = GameFactory(paused=True)
        response = authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert response.status_code == 200
        assert response.data["is_paused"] is False

    def test_unpausing_pushes_deadline_back(self, authenticated_client_factory):
        game = GameFactory(paused=True)
        client = authenticated_client_factory(game.created_by)
        before = _deadline(client, game)
        client.patch(_url(game.id))
        assert _deadline(client, game) > before

    def test_unpausing_notifies_players(self, authenticated_client_factory, assert_notification):
        player = UserFactory()
        game = GameFactory(paused=True, players=[player])
        authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert_notification(player, "game_resumed")

    def test_player_cannot_unpause_game(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(paused=True, players=[player])
        response = authenticated_client_factory(player).patch(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_GAME_MANAGER

    def test_cannot_unpause_running_game(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).patch(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_NOT_PAUSED

    def test_unauthenticated_user_cannot_unpause_game(self, unauthenticated_client):
        game = GameFactory(paused=True)
        response = unauthenticated_client.patch(_url(game.id))
        assert response.status_code == 401
