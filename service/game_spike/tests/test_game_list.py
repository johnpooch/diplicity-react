import pytest
from django.urls import reverse

from common.constants import Commitment, CommitmentRequirement, GameStatus
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db

URL = reverse("game_spike:game-list")


def _ids(response):
    return [game["id"] for game in response.data["results"]]


class TestGameList:
    def test_lists_games_newest_first(self, unauthenticated_client):
        older = GameFactory()
        newer = GameFactory()
        assert _ids(unauthenticated_client.get(URL)) == [newer.id, older.id]

    def test_sandbox_games_are_excluded_by_default(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True)
        assert _ids(authenticated_client_factory(game.created_by).get(URL)) == []

    def test_sandbox_filter_lists_sandbox_games(self, authenticated_client_factory):
        game = GameFactory(sandboxed=True)
        response = authenticated_client_factory(game.created_by).get(URL, {"sandbox": "true", "mine": "true"})
        assert _ids(response) == [game.id]

    def test_unauthenticated_users_do_not_see_private_games(self, unauthenticated_client):
        GameFactory(private=True)
        assert _ids(unauthenticated_client.get(URL)) == []

    def test_mine_lists_games_the_user_plays_or_masters(self, authenticated_client_factory):
        user = UserFactory()
        played = GameFactory(players=[user])
        mastered = GameFactory(created_by=user, as_game_master=True)
        GameFactory()
        response = authenticated_client_factory(user).get(URL, {"mine": "true"})
        assert set(_ids(response)) == {played.id, mastered.id}

    def test_can_join_lists_only_open_games_the_user_is_not_in(self, authenticated_client_factory):
        user = UserFactory()
        open_game = GameFactory()
        GameFactory(players=[user])
        GameFactory(active=True)
        response = authenticated_client_factory(user).get(URL, {"can_join": "true"})
        assert _ids(response) == [open_game.id]

    def test_eligible_only_hides_committed_games_from_medium_commitment(self, authenticated_client_factory):
        user = UserFactory(profile__commitment=Commitment.MEDIUM)
        open_game = GameFactory()
        GameFactory(commitment_requirement=CommitmentRequirement.COMMITTED)
        response = authenticated_client_factory(user).get(URL, {"eligible_only": "true"})
        assert _ids(response) == [open_game.id]

    def test_status_filter_accepts_several_statuses(self, unauthenticated_client):
        pending = GameFactory()
        active = GameFactory(active=True)
        GameFactory(completed=True)
        response = unauthenticated_client.get(URL, {"status": f"{GameStatus.PENDING},{GameStatus.ACTIVE}"})
        assert set(_ids(response)) == {pending.id, active.id}

    def test_unknown_status_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(URL, {"status": "lost"})
        assert response.status_code == 400

    def test_slots_remaining_ordering_lists_fullest_game_first(self, unauthenticated_client):
        emptier = GameFactory(players=1)
        fuller = GameFactory(players=4)
        response = unauthenticated_client.get(URL, {"ordering": "slots_remaining"})
        assert _ids(response) == [fuller.id, emptier.id]

    def test_deadline_ordering_lists_running_games_before_unscheduled_ones(self, unauthenticated_client):
        pending = GameFactory()
        active = GameFactory(active=True)
        response = unauthenticated_client.get(URL, {"ordering": "deadline"})
        assert _ids(response) == [active.id, pending.id]

    def test_unknown_ordering_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(URL, {"ordering": "random"})
        assert response.status_code == 400

    def test_list_includes_current_board(self, unauthenticated_client):
        GameFactory(active=True)
        current_phase = unauthenticated_client.get(URL).data["results"][0]["current_phase"]
        assert len(current_phase["units"]) == 22
        assert len(current_phase["supply_centers"]) == 22

    def test_query_count_does_not_grow_with_games(self, authenticated_client_factory, query_count):
        client = authenticated_client_factory(UserFactory())
        GameFactory(active=True)
        one_game = query_count(lambda: client.get(URL))
        GameFactory(active=True)
        GameFactory(players=3)
        assert query_count(lambda: client.get(URL)) == one_game
