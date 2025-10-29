import pytest
from django.urls import reverse
from rest_framework import status
from game.models import Game
from common.constants import GameStatus

join_viewname = "game-join"


@pytest.mark.django_db
def test_join_game_success(authenticated_client, pending_game_created_by_secondary_user, primary_user):
    """
    Test that an authenticated user can successfully join a game.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == primary_user.profile.name
    assert response.data["is_current_user"] is True


@pytest.mark.django_db
def test_join_game_unauthenticated(unauthenticated_client, pending_game_created_by_secondary_user):
    """
    Test that unauthenticated users cannot join a game.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_secondary_user.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_join_game_already_member(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that a user cannot join a game they are already a member of.
    """
    url = reverse(join_viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_join_game_non_pending(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that a user cannot join a game that is not in pending status.
    """
    game = pending_game_created_by_secondary_user
    game.status = GameStatus.ACTIVE
    game.save()

    url = reverse(join_viewname, args=[game.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_join_game_not_found(authenticated_client):
    """
    Test that attempting to join a non-existent game returns 404.
    """
    url = reverse(join_viewname, args=[999])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_join_game_max_players(
    authenticated_client, pending_game_created_by_secondary_user, italy_vs_germany_variant, tertiary_user
):
    """
    Test that a user cannot join a game that already has the maximum number of players.
    This simulates a scenario where the task worker failed to start the game after
    all players joined.
    """
    game = pending_game_created_by_secondary_user
    game.variant = italy_vs_germany_variant
    game.save()

    game.members.create(user=tertiary_user)

    url = reverse(join_viewname, args=[game.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# Leave/Delete Member Tests
leave_viewname = "game-leave"


@pytest.mark.django_db
def test_leave_game_success(
    authenticated_client, pending_game_created_by_secondary_user_joined_by_primary, primary_user
):
    """
    Test that an authenticated user can successfully leave a game.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user_joined_by_primary.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not pending_game_created_by_secondary_user_joined_by_primary.members.filter(user=primary_user).exists()


@pytest.mark.django_db
def test_leave_game_unauthenticated(unauthenticated_client, pending_game_created_by_secondary_user):
    """
    Test that unauthenticated users cannot leave a game.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user.id])
    response = unauthenticated_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_leave_game_not_a_member(authenticated_client, pending_game_created_by_secondary_user):
    """
    Test that a user cannot leave a game they are not a member of.
    """
    url = reverse(leave_viewname, args=[pending_game_created_by_secondary_user.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_leave_game_non_pending(authenticated_client, pending_game_created_by_secondary_user_joined_by_primary):
    """
    Test that a user cannot leave a game that is not in pending status.
    """
    game = pending_game_created_by_secondary_user_joined_by_primary
    game.status = GameStatus.ACTIVE
    game.save()

    url = reverse(leave_viewname, args=[game.id])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_leave_game_not_found(authenticated_client):
    """
    Test that attempting to leave a non-existent game returns 404.
    """
    url = reverse(leave_viewname, args=[999])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
