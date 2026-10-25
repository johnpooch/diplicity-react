import pytest
from django.urls import reverse

from common.constants import MyGameResult, MyGamesSection, MyGameStateKind
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:my-games-current")


def _sections(response):
    return {section["key"]: section["games"] for section in response.data["sections"]}


class TestMyGamesCurrent:
    def test_player_who_owes_orders_needs_to_act(self, authenticated_client_factory):
        game = GameFactory(active=True)
        sections = _sections(authenticated_client_factory(game.created_by).get(URL))
        row = sections[MyGamesSection.NEEDS_ATTENTION][0]
        assert row["id"] == game.id
        assert row["state"]["kind"] == MyGameStateKind.SUBMIT_ORDERS
        assert row["nation"] is not None

    def test_player_with_confirmed_orders_is_listed_as_active(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(active=True, players=[user], orders_confirmed_by=[user])
        sections = _sections(authenticated_client_factory(user).get(URL))
        assert sections[MyGamesSection.ACTIVE][0]["state"]["kind"] == MyGameStateKind.ORDERS_CONFIRMED

    def test_pending_game_reports_filled_seats(self, authenticated_client_factory):
        game = GameFactory(players=2)
        sections = _sections(authenticated_client_factory(game.created_by).get(URL))
        assert sections[MyGamesSection.PENDING][0]["seats"] == {"filled": 3, "total": 7}

    def test_unconfirmed_mustering_seat_needs_attention(self, authenticated_client_factory):
        game = GameFactory(mustering=True)
        sections = _sections(authenticated_client_factory(game.created_by).get(URL))
        assert sections[MyGamesSection.NEEDS_ATTENTION][0]["state"]["kind"] == MyGameStateKind.CONFIRM_SEAT

    def test_game_master_sees_game_under_managing(self, authenticated_client_factory):
        game = GameFactory(as_game_master=True, active=True)
        sections = _sections(authenticated_client_factory(game.created_by).get(URL))
        assert sections[MyGamesSection.MANAGING][0]["state"]["kind"] == MyGameStateKind.RESOLVING

    def test_sandbox_game_is_listed_under_sandbox(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True)
        sections = _sections(authenticated_client_factory(game.created_by).get(URL))
        assert sections[MyGamesSection.SANDBOX][0]["id"] == game.id

    def test_recently_won_game_reports_solo_victory(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(completed=True, players=[user], won_by=[user])
        row = _sections(authenticated_client_factory(user).get(URL))[MyGamesSection.RECENTLY_FINISHED][0]
        assert row["state"]["result"] == MyGameResult.SOLO_VICTORY

    def test_other_players_games_are_not_listed(self, authenticated_client_factory):
        GameFactory(active=True)
        response = authenticated_client_factory(UserFactory()).get(URL)
        assert response.data["sections"] == []

    def test_sections_follow_the_fixed_order(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(created_by=user, sandboxed=True)
        GameFactory(players=[user])
        GameFactory(active=True, players=[user])
        keys = [section["key"] for section in authenticated_client_factory(user).get(URL).data["sections"]]
        assert keys == [MyGamesSection.NEEDS_ATTENTION, MyGamesSection.PENDING, MyGamesSection.SANDBOX]

    def test_unauthenticated_user_cannot_list_games(self, unauthenticated_client):
        assert unauthenticated_client.get(URL).status_code == 401

    def test_query_count_does_not_grow_with_games(self, authenticated_client_factory, query_count):
        user = UserFactory()
        client = authenticated_client_factory(user)
        GameFactory(active=True, players=[user])
        one_game = query_count(lambda: client.get(URL))
        GameFactory(active=True, players=[user])
        GameFactory(players=[user])
        assert query_count(lambda: client.get(URL)) == one_game
