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
        "nation_assignment": "random",
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
    def test_high_creator_can_require_committed(
        self, authenticated_client, primary_user, classical_variant, set_commitment
    ):
        set_commitment(primary_user, Commitment.HIGH)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, commitment_requirement=CommitmentRequirement.COMMITTED
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.commitment_requirement == CommitmentRequirement.COMMITTED

    @pytest.mark.django_db
    @pytest.mark.parametrize("commitment", [Commitment.MEDIUM, Commitment.UNDEFINED])
    def test_non_high_creator_cannot_require_committed(
        self, authenticated_client, primary_user, classical_variant, set_commitment, commitment
    ):
        set_commitment(primary_user, commitment)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, commitment_requirement=CommitmentRequirement.COMMITTED
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "commitment_requirement" in response.data

    @pytest.mark.django_db
    def test_low_creator_cannot_create(
        self, authenticated_client, primary_user, classical_variant, set_commitment
    ):
        set_commitment(primary_user, Commitment.LOW)
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, create_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "commitment_requirement" in response.data

    @pytest.mark.django_db
    def test_low_game_master_can_create_private_game(
        self, authenticated_client, primary_user, classical_variant, set_commitment
    ):
        set_commitment(primary_user, Commitment.LOW)
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, private=True, game_master=True
        )
        response = authenticated_client.post(url, payload, format="json")
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
        assert response.data["commitment_requirement"] == CommitmentRequirement.COMMITTED

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "commitment,commitment_requirement,expected",
        [
            (Commitment.HIGH, CommitmentRequirement.COMMITTED, "eligible"),
            (Commitment.MEDIUM, CommitmentRequirement.COMMITTED, "committed_locked"),
            (Commitment.UNDEFINED, CommitmentRequirement.COMMITTED, "committed_locked"),
            (Commitment.MEDIUM, CommitmentRequirement.OPEN, "eligible"),
            (Commitment.LOW, CommitmentRequirement.OPEN, "low_locked"),
        ],
    )
    def test_list_exposes_commitment_eligibility(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment,
        commitment,
        commitment_requirement,
        expected,
    ):
        set_commitment(primary_user, commitment)
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
        assert listed["commitment_eligibility"] == expected


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
    def test_high_user_sees_all(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment,
    ):
        set_commitment(primary_user, Commitment.HIGH)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids

    @pytest.mark.django_db
    @pytest.mark.parametrize("commitment", [Commitment.MEDIUM, Commitment.UNDEFINED])
    def test_non_high_user_excludes_committed(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment,
        commitment,
    ):
        set_commitment(primary_user, commitment)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert games[CommitmentRequirement.OPEN].id in ids
        assert games[CommitmentRequirement.COMMITTED].id not in ids

    @pytest.mark.django_db
    def test_low_user_sees_none(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment,
    ):
        set_commitment(primary_user, Commitment.LOW)
        self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        response = authenticated_client.get(url)
        assert response.data["results"] == []

    @pytest.mark.django_db
    def test_eligible_only_absent_shows_all(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        game_factory,
        base_pending_phase,
        set_commitment,
    ):
        set_commitment(primary_user, Commitment.UNDEFINED)
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true"
        response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids
