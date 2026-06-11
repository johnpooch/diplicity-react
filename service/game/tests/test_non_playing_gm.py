import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from common.constants import DeadlineMode, MovementPhaseDuration
from draw_proposal.models import DrawProposal
from game import models
from user_profile.models import UserProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def game_with_non_playing_gm(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(gm_user=None):
        if gm_user is None:
            gm_user = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Non-playing GM Game",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
        )
        game.members.create(user=gm_user, is_game_master=True)

        for i in range(game.variant.nations.count()):
            other_user = User.objects.create_user(f"npm_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"NPM Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game
    return _create


class TestNonPlayingGMStart:
    def test_non_playing_gm_has_no_nation_after_start(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        gm_member = game.members.get(user=primary_user)
        assert gm_member.nation is None

    def test_non_playing_gm_has_no_phase_state(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        gm_member = game.members.get(user=primary_user)
        assert not gm_member.phase_states.exists()

    def test_all_playing_members_get_nations(self, game_with_non_playing_gm, primary_user):
        game = game_with_non_playing_gm()
        playing_members = game.members.exclude(user=primary_user)
        for member in playing_members:
            assert member.nation is not None

    def test_playing_gm_still_gets_nation(self, db, primary_user, classical_variant, adjudication_data_classical):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Playing GM Game",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=False,
        )
        game.members.create(user=primary_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"pgm_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"PGM Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        gm_member = game.members.get(user=primary_user)
        assert gm_member.nation is not None


class TestNonPlayingGMCreateEndpoint:
    def test_create_game_with_non_playing_gm(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "NPM Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": True,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
                "nonPlayingGm": True,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["non_playing_gm"] is True

    def test_create_game_with_non_playing_gm_requires_private(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "NPM Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": False,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
                "nonPlayingGm": True,
            },
            format="json",
        )
        assert response.status_code == 400

    def test_create_game_without_non_playing_gm_defaults_false(self, db, primary_user, api_client):
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(
            "/game/",
            {
                "name": "Normal Test",
                "variantId": "classical",
                "nationAssignment": "random",
                "private": False,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["non_playing_gm"] is False


class TestNonPlayingGMMemberName:
    def test_non_playing_gm_name_is_real_name(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        api_client.force_authenticate(user=primary_user)
        response = api_client.get(f"/game/{game.id}/")
        assert response.status_code == 200
        gm_member = next(m for m in response.data["members"] if m["is_game_master"])
        assert gm_member["name"] == primary_user.profile.name
        assert gm_member["user_id"] == primary_user.id

    def test_playing_gm_name_is_real_name(self, db, primary_user, classical_variant, adjudication_data_classical, api_client):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Playing GM Name Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=False,
        )
        game.members.create(user=primary_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"pgmn_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"PGMN Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        api_client.force_authenticate(user=primary_user)
        response = api_client.get(f"/game/{game.id}/")
        assert response.status_code == 200
        gm_member = next(m for m in response.data["members"] if m["is_game_master"])
        assert gm_member["name"] == primary_user.profile.name


class TestNonPlayingGMDrawProposals:
    def test_gm_can_create_draw_proposal(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        api_client.force_authenticate(user=primary_user)
        response = api_client.post(f"/games/{game.id}/draw-proposals/create/")
        assert response.status_code == 201
        assert DrawProposal.objects.filter(game=game).count() == 1
        proposal = DrawProposal.objects.get(game=game)
        gm_member = game.members.get(user=primary_user)
        assert proposal.created_by == gm_member
        assert not proposal.votes.filter(member=gm_member).exists()

    def test_gm_cannot_vote_on_draw_proposal(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        proposer = game.members.exclude(user=primary_user).first()
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=proposer)
        api_client.force_authenticate(user=primary_user)
        response = api_client.patch(
            f"/games/{game.id}/draw-proposals/{proposal.id}/vote/",
            {"accepted": True},
            format="json",
        )
        assert response.status_code == 403


class TestNonPlayingGMJoinTrigger:
    def test_full_api_flow_game_does_not_start_at_n_total_members(
        self, db, primary_user, secondary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany, api_client
    ):
        tertiary_user = User.objects.create_user("tertiary_full@test.com", password="testpass")
        UserProfile.objects.create(user=tertiary_user, name="Tertiary Full")

        from common.constants import GameStatus

        primary_client = APIClient()
        primary_client.force_authenticate(user=primary_user)
        secondary_client = APIClient()
        secondary_client.force_authenticate(user=secondary_user)
        tertiary_client = APIClient()
        tertiary_client.force_authenticate(user=tertiary_user)

        create_response = primary_client.post(
            "/game/",
            {
                "name": "Full API GM Test",
                "variantId": "italy-vs-germany",
                "nationAssignment": "random",
                "private": True,
                "deadlineMode": "duration",
                "movementPhaseDuration": "24 hours",
                "nonPlayingGm": True,
            },
            format="json",
        )
        assert create_response.status_code == 201
        assert create_response.data["non_playing_gm"] is True
        game_id = create_response.data["id"]

        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            join1 = secondary_client.post(f"/game/{game_id}/join/")
        assert join1.status_code == 201

        from game.models import Game
        game = Game.objects.get(id=game_id)
        assert game.status == GameStatus.PENDING, (
            f"Game started prematurely with only 1 non-GM player. "
            f"members.count()={game.members.count()}, "
            f"non_gm_count={game.members.filter(is_game_master=False).count()}, "
            f"non_playing_gm={game.non_playing_gm}"
        )

        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            join2 = tertiary_client.post(f"/game/{game_id}/join/")
        assert join2.status_code == 201

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

    def test_game_does_not_start_when_first_player_joins(
        self, db, primary_user, secondary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany, api_client
    ):
        from common.constants import GameStatus, MovementPhaseDuration, DeadlineMode
        from phase.models import Phase

        game = models.Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="GM Start Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)

        api_client.force_authenticate(user=secondary_user)
        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            response = api_client.post(f"/game/{game.id}/join/")

        assert response.status_code == 201
        game.refresh_from_db()
        assert game.status == GameStatus.PENDING, (
            "Game started with only 1 non-GM player for a 2-nation variant"
        )
        assert game.members.filter(is_game_master=False).count() == 1

    def test_game_starts_when_all_players_join(
        self, db, primary_user, secondary_user, italy_vs_germany_variant, adjudication_data_italy_vs_germany, api_client
    ):
        from common.constants import GameStatus, MovementPhaseDuration, DeadlineMode

        tertiary_user = User.objects.create_user("tertiary2@test.com", password="testpass")
        UserProfile.objects.create(user=tertiary_user, name="Tertiary Player")

        game = models.Game.objects.create_from_template(
            italy_vs_germany_variant,
            name="GM Full Start Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)

        secondary_client = APIClient()
        secondary_client.force_authenticate(user=secondary_user)
        tertiary_client = APIClient()
        tertiary_client.force_authenticate(user=tertiary_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            secondary_client.post(f"/game/{game.id}/join/")
            tertiary_client.post(f"/game/{game.id}/join/")

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE, "Game should start after all players join"
        playing_members = game.members.filter(is_game_master=False)
        for member in playing_members:
            assert member.nation is not None, "All non-GM players should have a nation"


class TestNonPlayingGMOrderAndPhasePermissions:
    def test_gm_cannot_delete_order(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        api_client.force_authenticate(user=primary_user)
        response = api_client.delete(f"/game/{game.id}/orders/delete/some-province")
        assert response.status_code == 403

    def test_gm_cannot_confirm_phase(self, game_with_non_playing_gm, primary_user, api_client):
        game = game_with_non_playing_gm()
        api_client.force_authenticate(user=primary_user)
        response = api_client.patch(f"/game/{game.id}/confirm-phase/", {}, format="json")
        assert response.status_code == 403


class TestNonPlayingGMLeave:
    def test_gm_leaving_promotes_first_player_as_playing_gm(self, db, primary_user, classical_variant, api_client):
        second_user = User.objects.create_user("second@test.com", password="testpass")
        UserProfile.objects.create(user=second_user, name="Second Player")
        third_user = User.objects.create_user("third@test.com", password="testpass")
        UserProfile.objects.create(user=third_user, name="Third Player")

        game = models.Game.objects.create_from_template(
            classical_variant,
            name="GM Leave Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)
        second_member = game.members.create(user=second_user)
        game.members.create(user=third_user)

        api_client.force_authenticate(user=primary_user)
        response = api_client.delete(f"/game/{game.id}/leave/")
        assert response.status_code == 204

        game.refresh_from_db()
        assert game.non_playing_gm is False
        second_member.refresh_from_db()
        assert second_member.is_game_master is True
        assert not game.members.filter(user=primary_user).exists()

    def test_gm_leaving_with_no_other_players_deletes_game(self, db, primary_user, classical_variant, api_client):
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="GM Leave Solo Test",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            non_playing_gm=True,
            private=True,
        )
        game.members.create(user=primary_user, is_game_master=True)

        api_client.force_authenticate(user=primary_user)
        response = api_client.delete(f"/game/{game.id}/leave/")
        assert response.status_code == 204

        from game.models import Game
        assert not Game.objects.filter(id=game.id).exists()
