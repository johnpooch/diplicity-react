import pytest
from django.urls import reverse

from common.constants import MovementPhaseDuration
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:game-fastest")


class TestGameFastest:
    def test_returns_fullest_joinable_game(self, authenticated_client_factory):
        GameFactory(players=2)
        fuller = GameFactory(players=4)
        response = authenticated_client_factory(UserFactory()).get(URL)
        assert response.status_code == 200
        assert response.data["game"]["id"] == fuller.id

    def test_ignores_games_with_fewer_than_three_players(self, authenticated_client_factory):
        GameFactory(players=1)
        response = authenticated_client_factory(UserFactory()).get(URL)
        assert response.data["game"] is None

    def test_ignores_games_with_short_phases(self, authenticated_client_factory):
        GameFactory(players=4, movement_phase_duration=MovementPhaseDuration.TWELVE_HOURS)
        response = authenticated_client_factory(UserFactory()).get(URL)
        assert response.data["game"] is None

    def test_ignores_games_the_user_already_joined(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(players=[user, UserFactory(), UserFactory()])
        response = authenticated_client_factory(user).get(URL)
        assert response.data["game"] is None

    def test_unauthenticated_user_cannot_search(self, unauthenticated_client):
        assert unauthenticated_client.get(URL).status_code == 401

    def test_query_count_does_not_grow_with_candidates(self, authenticated_client_factory, query_count):
        client = authenticated_client_factory(UserFactory())
        GameFactory(players=3)
        one_candidate = query_count(lambda: client.get(URL))
        GameFactory(players=3)
        GameFactory(players=4)
        assert query_count(lambda: client.get(URL)) == one_candidate
