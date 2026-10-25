import pytest
from django.urls import reverse

from common.constants import GameActionKey, MusterStatus, OrderStatus
from game_spike.factories import GameFactory, UserFactory

pytestmark = pytest.mark.django_db


def _url(game_id):
    return reverse("game_spike:game-retrieve", args=[game_id])


def _action_keys(response):
    return [action["key"] for action in response.data["actions"]]


class TestGameRetrieve:
    def test_anyone_can_retrieve_a_game(self, unauthenticated_client):
        game = GameFactory()
        response = unauthenticated_client.get(_url(game.id))
        assert response.status_code == 200
        assert response.data["id"] == game.id

    def test_unauthenticated_viewer_has_no_actions(self, unauthenticated_client):
        game = GameFactory()
        response = unauthenticated_client.get(_url(game.id))
        assert response.data["actions"] == []
        assert response.data["can_join"] is False

    def test_missing_game_returns_404(self, unauthenticated_client):
        response = unauthenticated_client.get(_url("missing-game"))
        assert response.status_code == 404

    def test_outsider_can_join_pending_game(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(UserFactory()).get(_url(game.id))
        assert response.data["can_join"] is True
        assert GameActionKey.JOIN in _action_keys(response)

    def test_player_cannot_join_game_again(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert response.data["can_join"] is False
        assert response.data["can_leave"] is True

    def test_game_master_can_assign_nations_in_pending_game(self, authenticated_client_factory):
        game = GameFactory(as_game_master=True)
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert GameActionKey.ASSIGN_NATIONS in _action_keys(response)
        assert response.data["game_master_member_id"] is not None

    def test_player_can_edit_nation_preferences_in_pending_game(self, authenticated_client_factory):
        game = GameFactory()
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert [action["key"] for action in response.data["player_list_actions"]] == [
            GameActionKey.EDIT_NATION_PREFERENCES
        ]

    def test_manager_can_pause_active_game(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert {GameActionKey.PAUSE, GameActionKey.EXTEND_DEADLINE} <= set(_action_keys(response))

    def test_player_cannot_pause_active_game(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, players=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        assert GameActionKey.PAUSE not in _action_keys(response)
        assert GameActionKey.WITHDRAW in _action_keys(response)

    def test_manager_can_unpause_paused_game(self, authenticated_client_factory):
        game = GameFactory(paused=True)
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert GameActionKey.UNPAUSE in _action_keys(response)
        assert GameActionKey.PAUSE not in _action_keys(response)
        assert response.data["is_paused"] is True

    def test_player_without_orders_has_orders_required(self, authenticated_client_factory):
        game = GameFactory(active=True)
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert response.data["order_status"] == OrderStatus.ORDERS_REQUIRED

    def test_player_with_unconfirmed_orders_has_orders_not_confirmed(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, players=[player], orders_submitted_by=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        assert response.data["order_status"] == OrderStatus.ORDERS_NOT_CONFIRMED

    def test_player_with_confirmed_orders_has_orders_submitted(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, players=[player], orders_confirmed_by=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        assert response.data["order_status"] == OrderStatus.ORDERS_SUBMITTED
        assert response.data["phase_confirmed"] is True

    def test_mustering_player_must_confirm_seat(self, authenticated_client_factory):
        game = GameFactory(mustering=True)
        response = authenticated_client_factory(game.created_by).get(_url(game.id))
        assert response.data["muster_status"] == MusterStatus.CONFIRMATION_REQUIRED
        assert GameActionKey.CONFIRM_SEAT in _action_keys(response)

    def test_mustered_player_has_confirmed_seat(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(mustering=True, players=[player], mustered=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        assert response.data["muster_status"] == MusterStatus.CONFIRMED
        assert GameActionKey.CONFIRM_SEAT not in _action_keys(response)

    def test_anonymous_game_hides_other_players(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, anonymous=True, players=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        others = [member for member in response.data["members"] if not member["is_current_user"]]
        assert {member["name"] for member in others} == {"Anonymous"}
        assert {member["user_id"] for member in others} == {None}

    def test_anonymous_game_shows_players_their_own_identity(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(active=True, anonymous=True, players=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        own = next(member for member in response.data["members"] if member["is_current_user"])
        assert own["user_id"] == player.id

    def test_completed_anonymous_game_reveals_players(self, authenticated_client_factory):
        player = UserFactory()
        game = GameFactory(completed=True, anonymous=True, players=[player])
        response = authenticated_client_factory(player).get(_url(game.id))
        assert "Anonymous" not in {member["name"] for member in response.data["members"]}

    def test_won_game_reports_victory(self, authenticated_client_factory):
        winner = UserFactory()
        game = GameFactory(completed=True, players=[winner], won_by=[winner])
        response = authenticated_client_factory(winner).get(_url(game.id))
        assert response.data["victory"]["type"] == "solo"
        assert [member["user_id"] for member in response.data["victory"]["members"]] == [winner.id]

    def test_unchanged_game_answers_poll_with_304(self, authenticated_client_factory):
        game = GameFactory(active=True)
        client = authenticated_client_factory(game.created_by)
        etag = client.get(_url(game.id))["ETag"]
        response = client.get(_url(game.id), HTTP_IF_NONE_MATCH=etag)
        assert response.status_code == 304

    def test_changed_game_answers_poll_with_new_etag(self, authenticated_client_factory):
        game = GameFactory(active=True)
        client = authenticated_client_factory(game.created_by)
        etag = client.get(_url(game.id))["ETag"]
        client.patch(reverse("game_spike:game-pause", args=[game.id]))
        response = client.get(_url(game.id), HTTP_IF_NONE_MATCH=etag)
        assert response.status_code == 200
        assert response["ETag"] != etag

    def test_query_count_does_not_grow_with_players(self, authenticated_client_factory, query_count):
        small = GameFactory(players=1)
        large = GameFactory(full=True)
        client = authenticated_client_factory(UserFactory())
        assert query_count(lambda: client.get(_url(small.id))) == query_count(lambda: client.get(_url(large.id)))
