import pytest
from django.urls import reverse

from common.constants import DeniedReason
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-delete", args=[game_id])


def _retrieve(client, game):
    return client.get(reverse("game_spike:game-retrieve", args=[game.id]))


class TestGameDelete:
    def test_game_master_can_delete_pending_game(self, authenticated_client_factory):
        game = GameFactory(as_game_master=True, players=2)
        client = authenticated_client_factory(game.created_by)
        response = client.delete(_url(game.id))
        assert response.status_code == 204
        assert _retrieve(client, game).status_code == 404

    def test_game_master_can_delete_mustering_game(self, authenticated_client_factory):
        game = GameFactory(as_game_master=True, mustering=True)
        response = authenticated_client_factory(game.created_by).delete(_url(game.id))
        assert response.status_code == 204

    def test_deleting_notifies_players_but_not_the_game_master(self, authenticated_client_factory, assert_notification):
        player = UserFactory()
        game = GameFactory(as_game_master=True, players=[player])
        authenticated_client_factory(game.created_by).delete(_url(game.id))
        assert_notification(player, "game_deleted")
        assert_notification(game.created_by, "game_deleted", sent=False)

    def test_game_master_cannot_delete_started_game(self, authenticated_client_factory):
        game = GameFactory(as_game_master=True, active=True)
        response = authenticated_client_factory(game.created_by).delete(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_STARTED

    def test_creator_without_game_master_role_cannot_delete_game(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(game.created_by).delete(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_GAME_MASTER

    def test_owner_can_delete_sandbox_game_without_notification(
        self, authenticated_client_factory, assert_notification
    ):
        game = GameFactory(sandboxed=True)
        response = authenticated_client_factory(game.created_by).delete(_url(game.id))
        assert response.status_code == 204
        assert_notification(game.created_by, "game_deleted", sent=False)

    def test_outsider_cannot_delete_sandbox_game(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True)
        response = authenticated_client_factory(UserFactory()).delete(_url(game.id))
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_PARTICIPANT

    def test_unauthenticated_user_cannot_delete_game(self, unauthenticated_client):
        game = GameFactory(as_game_master=True)
        response = unauthenticated_client.delete(_url(game.id))
        assert response.status_code == 401

    def test_deleting_missing_game_returns_404(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).delete(_url("missing-game"))
        assert response.status_code == 404
