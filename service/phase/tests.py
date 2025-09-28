import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock
from rest_framework import status
from common.constants import PhaseStatus
from .models import Phase
from .serializers import PhaseStateSerializer


@pytest.mark.django_db
def test_confirm_phase_success(
    authenticated_client, active_game_with_phase_state, secondary_user, classical_france_nation
):
    """
    Test that an authenticated user can successfully confirm their phase.
    """
    # Add secondary user so that phase doesn't resolve
    secondary_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    active_game_with_phase_state.current_phase.phase_states.create(member=secondary_member)

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


@pytest.mark.django_db
def test_phase_should_resolve_immediately_no_users_with_orders(active_game_with_phase_state):
    """
    Test that a phase should resolve immediately when no users have possible orders.
    """
    phase = active_game_with_phase_state.current_phase
    phase.options = {"England": {}}
    phase.save()
    assert phase.should_resolve_immediately


@pytest.mark.django_db
def test_phase_should_resolve_immediately_all_confirmed(active_game_with_phase_state):
    """
    Test that a phase should resolve immediately when all users with orders have confirmed.
    """
    phase = active_game_with_phase_state.current_phase
    phase.options = {"England": {"lon": {"Hold": [], "Move": ["nth"]}}}
    phase.save()
    assert not phase.should_resolve_immediately
    phase_state = phase.phase_states.first()
    phase_state.orders_confirmed = True
    phase_state.save()
    phase.refresh_from_db()
    assert phase.should_resolve_immediately


@pytest.mark.django_db
def test_phase_should_not_resolve_immediately_partial_confirmation(
    active_game_with_phase_state, secondary_user, classical_france_nation
):
    """
    Test that a phase should NOT resolve immediately when some users with orders haven't confirmed.
    """
    phase = active_game_with_phase_state.current_phase
    secondary_member = active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    phase.phase_states.create(member=secondary_member)
    phase.options = {
        "England": {"lon": {"Hold": [], "Move": ["nth"]}},
        "France": {"par": {"Hold": [], "Move": ["pic"]}},
    }
    phase.save()
    first_phase_state = phase.phase_states.first()
    first_phase_state.orders_confirmed = True
    first_phase_state.save()
    phase.refresh_from_db()
    assert not phase.should_resolve_immediately


@pytest.mark.django_db
def test_nations_with_possible_orders_various_scenarios():
    """
    Test the nations_with_possible_orders property with various option configurations.
    """
    phase = Phase()
    phase.options = {}
    assert len(phase.nations_with_possible_orders) == 0
    phase.options = {"England": {}, "France": {}}
    assert len(phase.nations_with_possible_orders) == 0
    phase.options = {"England": {"lon": {"Hold": [], "Move": ["nth"]}}, "France": {}}
    nations = phase.nations_with_possible_orders
    assert len(nations) == 1
    assert "England" in nations
    phase.options = {
        "England": {"lon": {"Hold": [], "Move": ["nth"]}},
        "France": {"par": {"Hold": [], "Move": ["pic"]}},
    }
    nations = phase.nations_with_possible_orders
    assert len(nations) == 2
    assert "England" in nations
    assert "France" in nations


@pytest.mark.django_db
def test_resolve_due_phases_with_scheduled_time(active_game_with_phase_state):
    """
    Test that resolve_due_phases resolves phases when scheduled time has passed.
    """
    phase = active_game_with_phase_state.current_phase
    past_time = timezone.now() - timedelta(hours=1)
    phase.scheduled_resolution = past_time
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 1
        assert result["failed"] == 0
        mock_resolve.assert_called_once_with(phase)


@pytest.mark.django_db
def test_resolve_due_phases_with_immediate_resolution(active_game_with_phase_state):
    """
    Test that resolve_due_phases resolves phases that should resolve immediately.
    """
    phase = active_game_with_phase_state.current_phase

    future_time = timezone.now() + timedelta(hours=24)
    phase.scheduled_resolution = future_time
    phase.options = {}
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 1
        assert result["failed"] == 0
        mock_resolve.assert_called_once_with(phase)


@pytest.mark.django_db
def test_resolve_due_phases_no_resolution_needed(active_game_with_phase_state):
    """
    Test that resolve_due_phases doesn't resolve phases that aren't ready.
    """
    phase = active_game_with_phase_state.current_phase

    future_time = timezone.now() + timedelta(hours=24)
    phase.scheduled_resolution = future_time
    phase.options = {"England": {"lon": {"Hold": [], "Move": ["nth"]}}}
    phase.save()
    with patch.object(Phase.objects, "resolve") as mock_resolve:
        result = Phase.objects.resolve_due_phases()
        assert result["resolved"] == 0
        assert result["failed"] == 0
        mock_resolve.assert_not_called()
