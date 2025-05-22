import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "game-confirm-phase"

@pytest.mark.django_db
def test_confirm_phase_success(authenticated_client, active_game_with_phase_state):
    """
    Test that an authenticated user can successfully confirm their phase.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    assert phase_state.orders_confirmed

@pytest.mark.django_db
def test_confirm_phase_already_confirmed(authenticated_client, active_game_with_confirmed_phase_state):
    """
    Test that confirming an already confirmed phase unconfirms it.
    """
    url = reverse(viewname, args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    
    phase_state = active_game_with_confirmed_phase_state.current_phase.phase_states.first()
    assert not phase_state.orders_confirmed

@pytest.mark.django_db
def test_confirm_phase_game_not_active(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that confirming a phase in a non-active game returns 400.
    """
    url = reverse(viewname, args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_confirm_phase_user_not_member(authenticated_client, active_game_created_by_secondary_user):
    """
    Test that a non-member cannot confirm a phase.
    """
    url = reverse(viewname, args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_confirm_phase_user_eliminated(authenticated_client_for_secondary_user, active_game_with_eliminated_member):
    """
    Test that an eliminated user cannot confirm a phase.
    """
    url = reverse(viewname, args=[active_game_with_eliminated_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_confirm_phase_user_kicked(authenticated_client_for_secondary_user, active_game_with_kicked_member):
    """
    Test that a kicked user cannot confirm a phase.
    """
    url = reverse(viewname, args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_confirm_phase_unauthenticated(unauthenticated_client, active_game_with_phase_state):
    """
    Test that unauthenticated users cannot confirm a phase.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_confirm_phase_auto_resolve_single_player(authenticated_client, active_game_with_resolution_task, mock_resolve_task):
    """
    Test that phase is auto-resolved when the only active player confirms orders.
    """
    url = reverse(viewname, args=[active_game_with_resolution_task.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify task was executed immediately
    mock_resolve_task.assert_called_once_with(
        args=[active_game_with_resolution_task.id], kwargs={}, task_id=active_game_with_resolution_task.resolution_task.id, countdown=0
    )

@pytest.mark.django_db
def test_confirm_phase_no_auto_resolve_kicked_player(authenticated_client, authenticated_client_for_secondary_user, active_game_with_kicked_member, mock_resolve_task):
    """
    Test that kicked player's confirmation doesn't trigger auto-resolve.
    """
    # Create a resolution task
    task = models.Task.objects.create()
    active_game_with_kicked_member.resolution_task = task
    active_game_with_kicked_member.save()
    
    # Kicked player confirms
    url = reverse(viewname, args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Active player confirms
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    
    mock_resolve_task.assert_called_once_with(
        args=[active_game_with_kicked_member.id], kwargs={}, task_id=task.id, countdown=0
    )

@pytest.mark.django_db
def test_unconfirm_phase_no_auto_resolve(authenticated_client, active_game_with_resolution_task, mock_resolve_task):
    """
    Test that unconfirming orders doesn't trigger auto-resolve.
    """
    # First confirm the orders
    phase_state = active_game_with_resolution_task.current_phase.phase_states.first()
    phase_state.orders_confirmed = True
    phase_state.save()
    
    # Then unconfirm
    url = reverse(viewname, args=[active_game_with_resolution_task.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    
    # Verify task was not executed
    mock_resolve_task.assert_not_called()
