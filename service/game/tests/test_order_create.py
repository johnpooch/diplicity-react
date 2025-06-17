import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "order-create"

@pytest.mark.django_db
def test_create_hold_valid(authenticated_client, active_game_with_phase_options):
    """
    Test creating a valid hold order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_hold_invalid(authenticated_client, active_game_with_phase_options):
    """
    Test creating an invalid hold order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "invalid_source",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_move_valid(authenticated_client, active_game_with_phase_options):
    """
    Test creating a valid move order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "target": "tri",
        "order_type": "Move",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_move_invalid(authenticated_client, active_game_with_phase_options):
    """
    Test creating an invalid move order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "target": "invalid_target",
        "order_type": "Move",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_support_valid(authenticated_client, active_game_with_phase_options):
    """
    Test creating a valid support order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "aux": "sev",
        "target": "rum",
        "order_type": "Support",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.django_db
def test_create_support_invalid(authenticated_client, active_game_with_phase_options):
    """
    Test creating an invalid support order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "aux": "invalid_aux",
        "target": "rum",
        "order_type": "Support",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_order_invalid_order_type(authenticated_client, active_game_with_phase_options):
    """
    Test creating an order with invalid order type.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "target": "tri",
        "order_type": "InvalidOrderType",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_order_game_not_found(authenticated_client):
    """
    Test creating an order for a non-existent game.
    """
    url = reverse(viewname, args=[999])
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_create_order_user_not_a_member(authenticated_client, active_game_with_phase_options):
    """
    Test creating an order when user is not a member of the game.
    """
    # Remove the user as a member
    active_game_with_phase_options.members.first().delete()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_create_order_game_not_active(authenticated_client, active_game_with_phase_options):
    """
    Test creating an order when game is not active.
    """
    active_game_with_phase_options.status = models.Game.PENDING
    active_game_with_phase_options.save()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_order_unauthorized(unauthenticated_client, active_game_with_phase_options):
    """
    Test creating an order when not authenticated.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = unauthenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_order_updates_existing_order(authenticated_client, active_game_with_phase_options):
    """
    Test that creating an order updates an existing order for the same source.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # First create a hold order
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    first_order_id = response.data["id"]

    # Then update it to a move order
    data = {
        "source": "bud",
        "target": "tri",
        "order_type": "Move",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    second_order_id = response.data["id"]

    # Verify it's the same order
    assert first_order_id == second_order_id
    assert response.data["order_type"] == "Move"
    assert response.data["source"] == "bud"
    assert response.data["target"] == "tri"

@pytest.mark.django_db
def test_create_order_different_source_creates_new_order(authenticated_client, active_game_with_phase_options):
    """
    Test that creating an order with a different source creates a new order.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Create first order
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    first_order_id = response.data["id"]

    # Create second order with different source
    data = {
        "source": "vie",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    second_order_id = response.data["id"]

    # Verify they are different orders
    assert first_order_id != second_order_id

@pytest.mark.django_db
def test_create_order_updates_maintain_validation(authenticated_client, active_game_with_phase_options):
    """
    Test that updating an order maintains validation.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # First create a valid order
    data = {
        "source": "bud",
        "order_type": "Hold",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Try to update with invalid data
    data = {
        "source": "bud",
        "target": "invalid_target",
        "order_type": "Move",
    }
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify the original order still exists and wasn't corrupted
    phase_state = active_game_with_phase_options.current_phase.phase_states.first()
    order = phase_state.orders.get(source="bud")
    assert order.order_type == "Hold"
    assert order.target is None 