import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_confirm_phase_success(
    authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
):
    """
    Test that an authenticated user can successfully confirm their phase.
    """
    # Add secondary user so that phase doesn't resolve
    active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    url = reverse("game-confirm-phase", args=[active_game_with_phase_state.id])
    response = authenticated_client.put(url)
    assert response.status_code == status.HTTP_200_OK

    phase_states = active_game_with_phase_state.current_phase.phase_states.all()
    phase_state = phase_states.first()
    phase_state.refresh_from_db()
    assert phase_state.orders_confirmed


@pytest.mark.django_db
def test_confirm_phase_already_confirmed(authenticated_client, active_game_with_confirmed_phase_state):
    """
    Test that confirming an already confirmed phase unconfirms it.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_confirmed_phase_state.id])
    response = authenticated_client.put(url)
    assert response.status_code == status.HTTP_200_OK

    phase_state = active_game_with_confirmed_phase_state.current_phase.phase_states.first()
    assert not phase_state.orders_confirmed


@pytest.mark.django_db
def test_confirm_phase_game_not_active(authenticated_client, pending_game_created_by_primary_user):
    """
    Test that confirming a phase in a non-active game returns 403.
    """
    url = reverse("game-confirm-phase", args=[pending_game_created_by_primary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_not_member(authenticated_client, active_game_created_by_secondary_user):
    """
    Test that a non-member cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_eliminated(authenticated_client_for_secondary_user, active_game_with_eliminated_member):
    """
    Test that an eliminated user cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_eliminated_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_user_kicked(authenticated_client_for_secondary_user, active_game_with_kicked_member):
    """
    Test that a kicked user cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_kicked_member.id])
    response = authenticated_client_for_secondary_user.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_confirm_phase_unauthenticated(unauthenticated_client, active_game_with_phase_state):
    """
    Test that unauthenticated users cannot confirm a phase.
    """
    url = reverse("game-confirm-phase", args=[active_game_with_phase_state.id])
    response = unauthenticated_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_retrieve_orderable_provinces_success(authenticated_client, active_game_with_phase_options):
    """
    Test that an authenticated member can retrieve orderable provinces.
    """
    url = reverse("phase-state-retrieve", args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert "orderable_provinces" in response.data


@pytest.mark.django_db
def test_retrieve_orderable_provinces_not_member(authenticated_client, active_game_created_by_secondary_user):
    """
    Test that a non-member cannot retrieve orderable provinces.
    """
    url = reverse("phase-state-retrieve", args=[active_game_created_by_secondary_user.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_resolve_phases_success(authenticated_client):
    """
    Test that the phase resolve endpoint works.
    """
    url = reverse("phase-resolve")
    response = authenticated_client.post(url)
    assert response.status_code == status.HTTP_200_OK
    assert "resolved" in response.data
    assert "failed" in response.data
