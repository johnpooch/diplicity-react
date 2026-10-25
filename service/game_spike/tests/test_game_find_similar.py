import pytest
from django.urls import reverse

from common.constants import MovementPhaseDuration
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:game-find-similar")
PARAMS = {"variant": "classical", "movement_phase_duration": MovementPhaseDuration.TWENTY_FOUR_HOURS}


class TestGameFindSimilar:
    def test_returns_fullest_matching_game(self, authenticated_client_factory):
        GameFactory(players=1)
        fuller = GameFactory(players=3)
        response = authenticated_client_factory(UserFactory()).get(URL, PARAMS)
        assert response.status_code == 200
        assert response.data["game"]["id"] == fuller.id

    def test_ignores_games_with_another_phase_length(self, authenticated_client_factory):
        GameFactory(movement_phase_duration=MovementPhaseDuration.FORTY_EIGHT_HOURS)
        response = authenticated_client_factory(UserFactory()).get(URL, PARAMS)
        assert response.data["game"] is None

    def test_ignores_games_the_user_already_joined(self, authenticated_client_factory):
        user = UserFactory()
        GameFactory(players=[user])
        response = authenticated_client_factory(user).get(URL, PARAMS)
        assert response.data["game"] is None

    def test_ignores_private_games(self, authenticated_client_factory):
        GameFactory(private=True)
        response = authenticated_client_factory(UserFactory()).get(URL, PARAMS)
        assert response.data["game"] is None

    def test_variant_and_phase_length_are_required(self, authenticated_client_factory):
        response = authenticated_client_factory(UserFactory()).get(URL)
        assert response.status_code == 400

    def test_unauthenticated_user_cannot_search(self, unauthenticated_client):
        assert unauthenticated_client.get(URL, PARAMS).status_code == 401

    def test_query_count_does_not_grow_with_candidates(self, authenticated_client_factory, query_count):
        client = authenticated_client_factory(UserFactory())
        GameFactory(players=2)
        one_candidate = query_count(lambda: client.get(URL, PARAMS))
        GameFactory(players=2)
        GameFactory(players=3)
        assert query_count(lambda: client.get(URL, PARAMS)) == one_candidate
