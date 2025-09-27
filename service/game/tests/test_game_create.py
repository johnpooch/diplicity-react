import pytest
from django.urls import reverse
from rest_framework import status
from game import models
from channel.models import Channel

viewname = "game-create"


@pytest.mark.django_db
def test_create_game_success(authenticated_client, classical_variant):
    """
    Test that an authenticated user can create a game successfully.
    """
    url = reverse(viewname)
    payload = {"name": "New Game", "variant": classical_variant.id}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert response.data["name"] == payload["name"]

    # Verify default nation assignment is random
    game = models.Game.objects.get(id=response.data["id"])
    assert game.nation_assignment == models.Game.RANDOM

    # Verify public channel was created
    channel = Channel.objects.filter(game=game).first()
    assert channel.name == "Public Press"
    assert not channel.private


@pytest.mark.django_db
def test_create_game_with_ordered_nation_assignment(authenticated_client, classical_variant):
    """
    Test that a game can be created with ordered nation assignment.
    """
    url = reverse(viewname)
    payload = {
        "name": "New Game",
        "variant": classical_variant.id,
        "nation_assignment": models.Game.ORDERED,
    }
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    game = models.Game.objects.get(id=response.data["id"])
    assert game.nation_assignment == models.Game.ORDERED

    # Verify public channel was created
    channel = Channel.objects.filter(game=game).first()
    assert channel is not None
    assert channel.name == "Public Press"
    assert not channel.private


@pytest.mark.django_db
def test_create_game_public_channel_unique(authenticated_client, classical_variant):
    """
    Test that each game gets its own unique public channel.
    """
    url = reverse(viewname)

    # Create first game
    payload1 = {"name": "Game 1", "variant": classical_variant.id}
    response1 = authenticated_client.post(url, payload1, format="json")
    game1 = models.Game.objects.get(id=response1.data["id"])
    channel1 = Channel.objects.get(game=game1)

    # Create second game
    payload2 = {"name": "Game 2", "variant": classical_variant.id}
    response2 = authenticated_client.post(url, payload2, format="json")
    game2 = models.Game.objects.get(id=response2.data["id"])
    channel2 = Channel.objects.get(game=game2)

    # Verify each game has its own channel
    assert channel1.id != channel2.id
    assert channel1.name == "Public Press"
    assert channel2.name == "Public Press"
    assert not channel1.private
    assert not channel2.private


@pytest.mark.django_db
def test_create_game_missing_name(authenticated_client, classical_variant):
    """
    Test that creating a game without a name returns 400.
    """
    url = reverse(viewname)
    payload = {"variant": classical_variant.id}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data


@pytest.mark.django_db
def test_create_game_missing_variant(authenticated_client):
    """
    Test that creating a game without a variant returns 400.
    """
    url = reverse(viewname)
    payload = {"name": "New Game"}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "variant" in response.data


@pytest.mark.django_db
def test_create_game_unauthenticated(unauthenticated_client, classical_variant):
    """
    Test that unauthenticated users cannot create a game.
    """
    url = reverse(viewname)
    payload = {"name": "New Game", "variant": classical_variant.id}
    response = unauthenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
