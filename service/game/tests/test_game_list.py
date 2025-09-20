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

@pytest.mark.django_db
def test_game_list_can_join_can_leave_flags_for_non_member(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that canJoin is true and canLeave is false for games the user hasn't joined.
    """
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # Find the game created by secondary user (primary user hasn't joined)
    game_data = next(g for g in response.data if g["name"] == pending_game_created_by_secondary_user.name)

    # User should be able to join but not leave
    assert game_data["can_join"] is True
    assert game_data["can_leave"] is False

@pytest.mark.django_db
def test_game_list_can_join_can_leave_flags_for_member(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that canJoin is false and canLeave is true for games the user has joined.
    """
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # Find the game created by primary user (primary user is member)
    game_data = next(g for g in response.data if g["name"] == pending_game_created_by_primary_user.name)

    # User should not be able to join but should be able to leave
    assert game_data["can_join"] is False
    assert game_data["can_leave"] is True

@pytest.mark.django_db
def test_game_list_can_join_can_leave_flags_for_active_games(authenticated_client, active_game_created_by_primary_user, active_game_created_by_secondary_user):
    """
    Test that both canJoin and canLeave are false for active games.
    """
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # Find active games
    primary_game_data = next(g for g in response.data if g["name"] == active_game_created_by_primary_user.name)
    secondary_game_data = next(g for g in response.data if g["name"] == active_game_created_by_secondary_user.name)

    # For active games, neither join nor leave should be allowed
    assert primary_game_data["can_join"] is False
    assert primary_game_data["can_leave"] is False
    assert secondary_game_data["can_join"] is False
    assert secondary_game_data["can_leave"] is False

@pytest.mark.django_db
def test_game_list_can_join_can_leave_flags_for_full_pending_game(authenticated_client, classical_variant, primary_user, secondary_user, tertiary_user, base_pending_phase):
    """
    Test that canJoin is false for a full pending game (all slots taken).
    """
    # Create a game and fill it with members (classical variant has 7 nations)
    game = models.Game.objects.create(
        name="Full Game",
        variant=classical_variant,
        status=models.Game.PENDING,
    )

    # Add a phase to the game
    base_pending_phase(game)

    # Add 3 different users for this test
    users = [primary_user, secondary_user, tertiary_user]
    nations = ["England", "France", "Germany"]
    for i, user in enumerate(users[:3]):
        game.members.create(user=user, nation=nations[i])

    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # Find the full game - primary user is a member so can_join should be False, can_leave should be True
    game_data = next(g for g in response.data if g["name"] == "Full Game")
    assert game_data["can_join"] is False  # User is already a member
    assert game_data["can_leave"] is True   # User can leave pending game

