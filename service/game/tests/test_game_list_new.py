import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from game import models
from rest_framework.test import APIClient

User = get_user_model()

url = reverse("game-list")

@pytest.mark.django_db
def test_game_list_unauthenticated(unauthenticated_client):
    """
    Test that unauthenticated users cannot access the game list.
    """
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_game_list_invalid_filter(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that invalid filters are ignored.
    """
    response = authenticated_client.get(url, {"invalid_filter": "true"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

@pytest.mark.django_db
def test_game_list_all_games(authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user):
    """
    Test that all games are returned when no filter is applied.
    """
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

@pytest.mark.django_db
def test_game_list_my_games(authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user):
    """
    Test that only games the user is a member of are returned with mine filter.
    """
    response = authenticated_client.get(url, {"mine": "true"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == pending_game_created_by_primary_user.name

@pytest.mark.django_db
def test_game_list_can_join(authenticated_client, pending_game_created_by_primary_user, pending_game_created_by_secondary_user):
    """
    Test that only games the user can join are returned with can_join filter.
    """
    response = authenticated_client.get(url, {"can_join": "true"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == pending_game_created_by_secondary_user.name

