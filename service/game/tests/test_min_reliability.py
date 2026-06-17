import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status

from game.models import Game
from common.constants import GameStatus, MinReliability

create_viewname = "game-create"
list_viewname = "game-list"
retrieve_viewname = "game-retrieve"


def create_payload(variant_id, **overrides):
    payload = {
        "name": "Reliability Game",
        "variant_id": variant_id,
        "nation_assignment": "random",
        "private": False,
        "deadline_mode": "duration",
        "movement_phase_duration": "24 hours",
    }
    payload.update(overrides)
    return payload


class TestGameCreateMinReliability:

    @pytest.mark.django_db
    def test_defaults_to_open(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        response = authenticated_client.post(
            url, create_payload(classical_variant.id), format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.min_reliability == MinReliability.OPEN

    @pytest.mark.django_db
    def test_persists_provided_value(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, min_reliability=MinReliability.RELIABLE_AND_NEW
        )
        with patch(
            "game.serializers.get_player_stats",
            return_value={"reliability_tier": "reliable"},
        ):
            response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(id=response.data["id"])
        assert game.min_reliability == MinReliability.RELIABLE_AND_NEW

    @pytest.mark.django_db
    def test_invalid_value_rejected(self, authenticated_client, classical_variant):
        url = reverse(create_viewname)
        payload = create_payload(classical_variant.id, min_reliability="bogus")
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_unreliable_creator_blocked_from_reliable_only(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id, min_reliability=MinReliability.RELIABLE_ONLY
        )
        with patch(
            "game.serializers.get_player_stats",
            return_value={"reliability_tier": None},
        ):
            response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "min_reliability" in response.data

    @pytest.mark.django_db
    def test_unreliable_game_master_can_create_reliable_only(
        self, authenticated_client, classical_variant
    ):
        url = reverse(create_viewname)
        payload = create_payload(
            classical_variant.id,
            min_reliability=MinReliability.RELIABLE_ONLY,
            private=True,
            game_master=True,
        )
        with patch(
            "game.serializers.get_player_stats",
            return_value={"reliability_tier": None},
        ):
            response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestMinReliabilitySerializerExposure:

    @pytest.mark.django_db
    def test_retrieve_exposes_min_reliability(
        self, authenticated_client, classical_variant, primary_user
    ):
        game = Game.objects.create(
            name="Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            min_reliability=MinReliability.RELIABLE_ONLY,
        )
        game.members.create(user=primary_user)
        url = reverse(retrieve_viewname, args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["min_reliability"] == MinReliability.RELIABLE_ONLY


class TestEligibleOnlyFilter:

    def _make_games(self, game_factory, variant, base_pending_phase):
        games = {}
        for value in (
            MinReliability.OPEN,
            MinReliability.RELIABLE_AND_NEW,
            MinReliability.RELIABLE_ONLY,
        ):
            game = game_factory(
                variant=variant,
                status=GameStatus.PENDING,
                private=False,
                min_reliability=value,
            )
            base_pending_phase(game)
            games[value] = game
        return games

    @pytest.mark.django_db
    def test_reliable_user_sees_all(
        self, authenticated_client, classical_variant, game_factory, base_pending_phase
    ):
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        with patch(
            "game.filters.get_player_stats",
            return_value={"reliability_tier": "reliable"},
        ):
            response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids

    @pytest.mark.django_db
    def test_new_user_excludes_reliable_only(
        self, authenticated_client, classical_variant, game_factory, base_pending_phase
    ):
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        with patch(
            "game.filters.get_player_stats",
            return_value={"reliability_tier": "new"},
        ):
            response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert games[MinReliability.OPEN].id in ids
        assert games[MinReliability.RELIABLE_AND_NEW].id in ids
        assert games[MinReliability.RELIABLE_ONLY].id not in ids

    @pytest.mark.django_db
    def test_unreliable_user_only_open(
        self, authenticated_client, classical_variant, game_factory, base_pending_phase
    ):
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true&eligible_only=true"
        with patch(
            "game.filters.get_player_stats",
            return_value={"reliability_tier": None},
        ):
            response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert games[MinReliability.OPEN].id in ids
        assert games[MinReliability.RELIABLE_AND_NEW].id not in ids
        assert games[MinReliability.RELIABLE_ONLY].id not in ids

    @pytest.mark.django_db
    def test_eligible_only_absent_shows_all(
        self, authenticated_client, classical_variant, game_factory, base_pending_phase
    ):
        games = self._make_games(game_factory, classical_variant, base_pending_phase)
        url = reverse(list_viewname) + "?can_join=true"
        with patch(
            "game.filters.get_player_stats",
            return_value={"reliability_tier": None},
        ):
            response = authenticated_client.get(url)
        ids = {g["id"] for g in response.data["results"]}
        assert {g.id for g in games.values()} <= ids
