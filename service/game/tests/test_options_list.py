import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from game import models
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_options_list_unauthenticated(unauthenticated_client, active_game_with_phase_options):
    """
    Test that unauthenticated users cannot access the options list.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_options_list_not_member(authenticated_client_for_secondary_user, active_game_with_phase_options):
    """
    Test that non-members cannot access the options list.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    response = authenticated_client_for_secondary_user.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_options_list_success(authenticated_client, active_game_with_phase_options):
    """
    Test that members can successfully retrieve the options list.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    
    # Check that each option has the expected structure
    for option in response.data:
        assert "province" in option
        assert "unit" in option
        
        # Check province structure
        province = option["province"]
        assert "id" in province
        assert "name" in province
        assert "type" in province
        assert "supply_center" in province
        
        # Unit can be null or have the expected structure
        if option["unit"] is not None:
            unit = option["unit"]
            assert "type" in unit
            assert "nation" in unit
            assert "province" in unit


@pytest.mark.django_db
def test_options_list_game_not_found(authenticated_client, active_game_with_phase_options):
    """
    Test that a 404 is returned for non-existent games.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": "non-existent", "phase_id": phase.id})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_options_list_phase_not_found(authenticated_client, active_game_with_phase_options):
    """
    Test that a 404 is returned for non-existent phases.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": 99999})
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
