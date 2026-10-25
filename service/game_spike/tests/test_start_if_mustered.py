from datetime import timedelta

import pytest
from django.urls import reverse

from common.constants import GameStatus
from game_spike.factories import GameFactory, UserFactory
from game_spike.tasks import start_if_mustered

pytestmark = pytest.mark.django_db

PASSED = timedelta(minutes=-1)


def _retrieve(client, game):
    return client.get(reverse("game_spike:game-retrieve", args=[game.id])).data


def _member(response, user):
    return next(member for member in response["members"] if member["user_id"] == user.id)


class TestStartIfMustered:
    def test_starts_game_once_every_player_is_mustered(self, unauthenticated_client):
        game = GameFactory(mustering=True, mustered=True)
        start_if_mustered(game_id=game.id)
        assert _retrieve(unauthenticated_client, game)["status"] == GameStatus.ACTIVE

    def test_waits_for_unmustered_players_before_deadline(self, unauthenticated_client):
        game = GameFactory(mustering=True)
        start_if_mustered(game_id=game.id)
        assert _retrieve(unauthenticated_client, game)["status"] == GameStatus.MUSTERING

    def test_starts_game_at_deadline_and_removes_no_shows(self, unauthenticated_client):
        no_show = UserFactory()
        game = GameFactory(mustering=True, players=[no_show], muster_ends_in=PASSED)
        start_if_mustered(game_id=game.id)
        response = _retrieve(unauthenticated_client, game)
        assert response["status"] == GameStatus.ACTIVE
        assert _member(response, no_show)["kicked"] is True

    def test_mustered_players_keep_their_seats(self, unauthenticated_client):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], mustered=[player], muster_ends_in=PASSED)
        start_if_mustered(game_id=game.id)
        assert _member(_retrieve(unauthenticated_client, game), player)["kicked"] is False

    def test_no_shows_are_told_they_lost_their_seat(self, assert_notification):
        no_show = UserFactory()
        game = GameFactory(mustering=True, players=[no_show], muster_ends_in=PASSED)
        start_if_mustered(game_id=game.id)
        assert_notification(no_show, "removed_from_muster")
        assert_notification(no_show, "game_start", sent=False)

    def test_mustered_players_are_told_the_game_started(self, assert_notification):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], mustered=[player], muster_ends_in=PASSED)
        start_if_mustered(game_id=game.id)
        assert_notification(player, "game_start")

    def test_does_nothing_for_game_that_already_started(self, assert_notification):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        start_if_mustered(game_id=game.id)
        assert_notification(player, "game_start", sent=False)

    def test_does_nothing_for_deleted_game(self):
        start_if_mustered(game_id="missing-game")
