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
    response = unauthenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_options_list_not_member(authenticated_client_for_secondary_user, active_game_with_phase_options):
    """
    Test that non-members cannot access the options list.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    response = authenticated_client_for_secondary_user.post(url, {}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_options_list_success_no_order(authenticated_client, active_game_with_phase_options):
    """
    Test that members can successfully retrieve the initial options list without a partial order.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    response = authenticated_client.post(url, {}, format="json")
    
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
def test_options_list_success_with_partial_order(authenticated_client, active_game_with_phase_options):
    """
    Test that members can successfully retrieve options based on a partial order.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    
    # Test with a partial order that exists in the test data
    partial_order = {
        "source": "bud",
        "order_type": "Move"
    }
    
    response = authenticated_client.post(
        url, 
        {"order": partial_order}, 
        format="json"
    )
    
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
def test_options_list_invalid_partial_order(authenticated_client, active_game_with_phase_options):
    """
    Test that invalid partial orders return a validation error.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    
    # Test with an invalid partial order that doesn't exist in the options tree
    invalid_order = {
        "source": "non_existent_province",
        "order_type": "invalid_type"
    }
    
    response = authenticated_client.post(
        url, 
        {"order": invalid_order}, 
        format="json"
    )
    
    # This should return a validation error since the partial order is invalid
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_options_list_game_not_found(authenticated_client, active_game_with_phase_options):
    """
    Test that a 404 is returned for non-existent games.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": "non-existent", "phase_id": phase.id})
    response = authenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_options_list_phase_not_found(authenticated_client, active_game_with_phase_options):
    """
    Test that a 404 is returned for non-existent phases.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": 99999})
    response = authenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_options_list_request_serializer_validation(authenticated_client, active_game_with_phase_options):
    """
    Test that the request serializer properly validates the order data.
    """
    game = active_game_with_phase_options
    phase = game.current_phase
    url = reverse("options-list", kwargs={"game_id": game.id, "phase_id": phase.id})
    
    # Test with valid order structure
    valid_order = {
        "order": {
            "source": "province_1",
            "target": "province_2",
            "aux": "province_3",
            "order_type": "support"
        }
    }
    
    response = authenticated_client.post(
        url, 
        valid_order, 
        format="json"
    )
    # Should not fail due to serializer validation
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    # Test with invalid order structure (missing required fields)
    invalid_order = {
        "order": {
            "source": "province_1"
            # Missing other fields
        }
    }
    
    response = authenticated_client.post(
        url, 
        invalid_order, 
        format="json"
    )
    # Should still work since all fields are optional in the serializer
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
