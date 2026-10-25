from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from common.constants import DeniedReason, MovementPhaseDuration
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-extend-deadline", args=[game_id])


def _deadline(client):
    response = client.get(reverse("game_spike:game-list"), {"mine": "true"})
    return parse_datetime(response.data["results"][0]["current_phase"]["scheduled_resolution"])


class TestGameExtendDeadline:
    def test_manager_can_extend_deadline_by_duration(self, authenticated_client_factory):
        game = GameFactory(active=True)
        client = authenticated_client_factory(game.created_by)
        before = _deadline(client)
        response = client.patch(_url(game.id), {"duration": MovementPhaseDuration.ONE_HOUR}, format="json")
        assert response.status_code == 200
        assert _deadline(client) - before == timedelta(hours=1)

    def test_extending_notifies_players(self, authenticated_client_factory, assert_notification):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        authenticated_client_factory(game.created_by).patch(
            _url(game.id), {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert_notification(player, "game_deadline_extended")

    def test_duration_is_required(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).patch(_url(game.id), {}, format="json")
        assert response.status_code == 400
        assert "duration" in response.data

    def test_unknown_duration_is_rejected(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).patch(
            _url(game.id), {"duration": "3 hours"}, format="json"
        )
        assert response.status_code == 400

    def test_player_cannot_extend_deadline(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        response = authenticated_client_factory(player).patch(
            _url(game.id), {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NOT_GAME_MANAGER

    def test_cannot_extend_deadline_of_paused_game(self, authenticated_client_factory):
        game = GameFactory(paused=True)
        response = authenticated_client_factory(game.created_by).patch(
            _url(game.id), {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.GAME_PAUSED

    def test_cannot_extend_deadline_of_untimed_game(self, authenticated_client_factory):
        game = GameFactory(active=True, movement_phase_duration=None)
        response = authenticated_client_factory(game.created_by).patch(
            _url(game.id), {"duration": MovementPhaseDuration.ONE_HOUR}, format="json"
        )
        assert response.status_code == 403
        assert response.data["detail"].code == DeniedReason.NO_SCHEDULED_RESOLUTION
