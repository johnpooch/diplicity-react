import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game
from common.constants import Commitment, CommitmentRequirement, GameStatus

create_viewname = "game-create"
list_viewname = "game-list"
retrieve_viewname = "game-retrieve"


def create_payload(variant_id, **overrides):
    payload = {
        "name": "Commitment Game",
        "variant_id": variant_id,
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    return payload


class TestGameCreateCommitmentRequirement:

    @pytest.mark.django_db
    def test_defaults_to_open(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, create_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.commitment_requirement == CommitmentRequirement.OPEN

    @pytest.mark.django_db
    @pytest.mark.parametrize("total", [10, 25])
    def test_creator_at_or_above_threshold_can_require_committed(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        set_commitment_total,
        total,
    ):
        set_commitment_total(primary_user, total)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, commitment_requirement=CommitmentRequirement.COMMITTED
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.commitment_requirement == CommitmentRequirement.COMMITTED

    @pytest.mark.django_db
    @pytest.mark.parametrize("total", [9, 0, -5])
    def test_creator_below_threshold_cannot_require_committed(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        set_commitment_total,
        total,
    ):
        set_commitment_total(primary_user, total)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, commitment_requirement=CommitmentRequirement.COMMITTED
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {"code": "commitment_too_low"}
        assert not Game.objects.filter(name="Commitment Game").exists()

    @pytest.mark.django_db
    def test_creator_below_threshold_cannot_require_committed_in_private_game(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        set_commitment_total,
    ):
        set_commitment_total(primary_user, 9)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id,
            private=True,
            commitment_requirement=CommitmentRequirement.COMMITTED,
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    @pytest.mark.parametrize("private", [False, True])
    def test_creator_with_negative_total_can_create_open_game(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        set_commitment_total,
        private,
    ):
        set_commitment_total(primary_user, -20)
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, create_payload(classical_variant.id, private=private), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.members.filter(user=primary_user).exists()

    @pytest.mark.django_db
    def test_low_tier_creator_can_create_public_game(
        self, authenticated_client, primary_user, classical_variant, set_commitment
    ):
        set_commitment(primary_user, Commitment.LOW)
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, create_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_invalid_value_rejected(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = create_payload(classical_variant.id, commitment_requirement="bogus")
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCommitmentRequirementSerializerExposure:

    @pytest.mark.django_db
    def test_retrieve_exposes_commitment_requirement(
        self, authenticated_client, classical_variant, primary_user
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            commitment_requirement=CommitmentRequirement.COMMITTED,
        )
        game.members.create(user=primary_user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["commitment_requirement"] == CommitmentRequirement.COMMITTED
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "total,commitment_requirement,can_join,join_blocked_reason",
        [
            (10, CommitmentRequirement.COMMITTED, True, None),
            (9, CommitmentRequirement.COMMITTED, False, "commitment_too_low"),
            (0, CommitmentRequirement.COMMITTED, False, "commitment_too_low"),
            (0, CommitmentRequirement.OPEN, True, None),
            (-20, CommitmentRequirement.OPEN, True, None),
        ],
    )
    def test_list_exposes_join_decision(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
        total,
        commitment_requirement,
        can_join,
        join_blocked_reason,
    ):
        set_commitment_total(primary_user, total)
        game = game_factory(
            variant=classical_variant,
            status=GameStatus.PENDING,
            private=False,
            commitment_requirement=commitment_requirement,
        )
        base_pending_phase(game)
        url = reverse(list_viewname) + "?can_join=true"
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        listed = next(g for g in response.data["results"] if g["id"] == game.id)
        assert listed["can_join"] is can_join
        assert listed["join_blocked_reason"] == join_blocked_reason

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "total,can_join,join_action",
        [
            (10, True, {"key": "join", "blocked_reason": None}),
            (9, False, {"key": "join", "blocked_reason": "commitment_too_low"}),
        ],
    )
    def test_retrieve_exposes_join_decision(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
        total,
        can_join,
        join_action,
    ):
        set_commitment_total(primary_user, total)
        game = game_factory(
            variant=classical_variant,
            status=GameStatus.PENDING,
            private=True,
            commitment_requirement=CommitmentRequirement.COMMITTED,
        )
        base_pending_phase(game)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_join"] is can_join
        assert response.data["join_blocked_reason"] == join_action["blocked_reason"]
        assert join_action in response.data["actions"]

    @pytest.mark.django_db
    def test_member_has_no_join_blocked_reason(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
    ):
        set_commitment_total(primary_user, 0)
        game = game_factory(
            variant=classical_variant,
            status=GameStatus.PENDING,
            private=False,
            commitment_requirement=CommitmentRequirement.COMMITTED,
        )
        base_pending_phase(game)
        game.members.create(user=primary_user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.data["can_join"] is False
        assert response.data["join_blocked_reason"] is None
        assert "join" not in [action["key"] for action in response.data["actions"]]


class TestEligibleOnlyFilter:

    def _make_games(self, game_factory, variant, base_pending_phase):
        games = {}
        for value in (
            CommitmentRequirement.OPEN,
            CommitmentRequirement.COMMITTED,
        ):
            game = game_factory(
                variant=variant,
                status=GameStatus.PENDING,
                private=False,
                commitment_requirement=value,
            )
            base_pending_phase(game)
            games[value] = game
        return games

    @pytest.mark.django_db
    def test_user_at_threshold_sees_all(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
    ):
        set_commitment_total(primary_user, 10)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids

    @pytest.mark.django_db
    @pytest.mark.parametrize("total", [9, 0, -15])
    def test_user_below_threshold_sees_only_open_games(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
        total,
    ):
        set_commitment_total(primary_user, total)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert games[CommitmentRequirement.OPEN].id in ids
        assert games[CommitmentRequirement.COMMITTED].id not in ids

    @pytest.mark.django_db
    def test_eligible_only_absent_shows_all(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment_total,
    ):
        set_commitment_total(primary_user, 0)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids
