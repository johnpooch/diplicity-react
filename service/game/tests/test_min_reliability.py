import pytest
from django.urls import reverse
from rest_framework import status

from game.models import Game
from common.constants import GameStatus, MinReliability

create_viewname = "game-create"
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
