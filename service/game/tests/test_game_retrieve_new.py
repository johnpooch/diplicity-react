import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "game-retrieve"

@pytest.mark.django_db
def test_retrieve_game(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that an authenticated user can retrieve a game they are a member of.
    """
    url = reverse(viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == pending_game_created_by_primary_user.id
    assert response.data["name"] == pending_game_created_by_primary_user.name

@pytest.mark.django_db
def test_retrieve_game_unauthenticated(unauthenticated_client, pending_game_created_by_primary_user):
    """
    Test that unauthenticated users cannot retrieve a game.
    """
    url = reverse(viewname, args=[pending_game_created_by_primary_user.id])
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_retrieve_game_not_found(authenticated_client):
    """
    Test that retrieving a non-existent game returns 404.
    """
    url = reverse(viewname, args=[999])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_phase_confirmed_true(authenticated_client, active_game_with_confirmed_phase_state):
    """
    Test that phase_confirmed is true when the user has confirmed their orders.
    """
    url = reverse(viewname, args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["phase_confirmed"]

@pytest.mark.django_db
def test_phase_confirmed_false(authenticated_client, active_game_with_phase_state):
    """
    Test that phase_confirmed is false when the user has not confirmed their orders.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["phase_confirmed"]

@pytest.mark.django_db
def test_phase_confirmed_inactive_phase(authenticated_client, active_game_with_confirmed_phase_state):
    """
    Test that phase_confirmed is false when the phase is inactive.
    """
    # Change phase to inactive
    phase = active_game_with_confirmed_phase_state.current_phase
    phase.status = models.Phase.COMPLETED
    phase.save()

    url = reverse(viewname, args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["phase_confirmed"]

@pytest.mark.django_db
def test_phase_confirmed_other_user(authenticated_client_for_secondary_user, active_game_with_confirmed_phase_state):
    """
    Test that phase_confirmed is false for other users.
    """
    url = reverse(viewname, args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client_for_secondary_user.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["phase_confirmed"]

@pytest.mark.django_db
def test_can_confirm_phase_true(authenticated_client, active_game_with_phase_state):
    """
    Test that can_confirm_phase is true for active members.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["can_confirm_phase"]

@pytest.mark.django_db
def test_can_confirm_phase_false_eliminated(authenticated_client_for_secondary_user, active_game_with_eliminated_member):
    """
    Test that can_confirm_phase is false for eliminated members.
    """
    url = reverse(viewname, args=[active_game_with_eliminated_member.id])
    response = authenticated_client_for_secondary_user.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["can_confirm_phase"]

@pytest.mark.django_db
def test_can_confirm_phase_false_kicked(authenticated_client_for_secondary_user, active_game_with_kicked_member):
    """
    Test that can_confirm_phase is false for kicked members.
    """
    url = reverse(viewname, args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["can_confirm_phase"]

@pytest.mark.django_db
def test_can_confirm_phase_false_inactive_phase(authenticated_client, active_game_with_phase_state):
    """
    Test that can_confirm_phase is false when the phase is inactive.
    """
    # Change phase to inactive
    phase = active_game_with_phase_state.current_phase
    phase.status = models.Phase.COMPLETED
    phase.save()

    url = reverse(viewname, args=[active_game_with_phase_state.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["can_confirm_phase"]

@pytest.mark.django_db
def test_can_confirm_phase_false_non_member(authenticated_client_for_secondary_user, active_game_created_by_primary_user):
    """
    Test that can_confirm_phase is false for non-members.
    """
    url = reverse(viewname, args=[active_game_created_by_primary_user.id])
    response = authenticated_client_for_secondary_user.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["can_confirm_phase"]

@pytest.mark.django_db
def test_game_without_phases(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that phase properties are false when a game has no phases.
    """
    url = reverse(viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["phase_confirmed"]
    assert not response.data["can_confirm_phase"]
