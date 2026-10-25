import pytest
from django.urls import reverse

from common.constants import MyGameResult, MyGameStateKind
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:my-games-finished")


def _ids(response):
    return [game["id"] for game in response.data["results"]]


class TestMyGamesFinished:
    def test_finished_game_is_listed_with_its_result(self, authenticated_client_factory):
        user = UserFactory()
        game = GameFactory(completed=True, players=[user], won_by=[user])
        row = authenticated_client_factory(user).get(URL).data["results"][0]
        assert row["id"] == game.id
        assert row["state"]["kind"] == MyGameStateKind.FINISHED
        assert row["state"]["result"] == MyGameResult.SOLO_VICTORY

    def test_lost_game_names_the_winner(self, authenticated_client_factory):
        user = UserFactory()
        winner = UserFactory()
        GameFactory(completed=True, players=[user, winner], won_by=[winner])
        row = authenticated_client_factory(user).get(URL).data["results"][0]
        assert row["state"]["result"] == MyGameResult.WON_BY
        assert row["state"]["winner"] is not None

    def test_running_games_are_not_listed(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(active=True, players=[user])
        assert _ids(authenticated_client_factory(user).get(URL)) == []

    def test_sandbox_games_are_not_listed(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True, completed_now=True)
        assert _ids(authenticated_client_factory(game.created_by).get(URL)) == []

    def test_most_recently_finished_game_comes_first(self, authenticated_client_factory):
        user = UserFactory()
        first = GameFactory(completed=True, players=[user])
        second = GameFactory(completed=True, players=[user])
        assert _ids(authenticated_client_factory(user).get(URL)) == [second.id, first.id]

    def test_unauthenticated_user_cannot_list_games(self, unauthenticated_client):
        assert unauthenticated_client.get(URL).status_code == 401

    def test_query_count_does_not_grow_with_games(self, authenticated_client_factory, query_count):
        user = UserFactory()
        client = authenticated_client_factory(user)
        GameFactory(completed=True, players=[user])
        one_game = query_count(lambda: client.get(URL))
        GameFactory(completed=True, players=[user])
        GameFactory(completed=True, players=[user])
        assert query_count(lambda: client.get(URL)) == one_game
