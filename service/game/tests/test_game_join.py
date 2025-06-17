import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "game-join"

@pytest.mark.django_db
def test_join_game_success(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that an authenticated user can successfully join a game.
    """
    url = reverse(viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == pending_game_created_by_secondary_user.id
    assert response.data["name"] == pending_game_created_by_secondary_user.name

@pytest.mark.django_db
def test_join_game_unauthenticated(unauthenticated_client, pending_game_created_by_secondary_user):
    """
    Test that unauthenticated users cannot join a game.
    """
    url = reverse(viewname, args=[pending_game_created_by_secondary_user.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_join_game_already_member(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that a user cannot join a game they are already a member of.
    """
    url = reverse(viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_join_game_non_pending(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that a user cannot join a game that is not in pending status.
    """
    game = pending_game_created_by_secondary_user
    game.status = models.Game.ACTIVE
    game.save()

    url = reverse(viewname, args=[game.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_join_game_not_found(authenticated_client):
    """
    Test that attempting to join a non-existent game returns 404.
    """
    url = reverse(viewname, args=[999])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
