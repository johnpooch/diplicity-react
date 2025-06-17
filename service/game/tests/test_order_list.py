import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "order-list"

@pytest.mark.django_db
def test_list_orders_active_phase(authenticated_client, active_game_with_multiple_orders):
    """
    Test listing orders in an active phase.
    """
    game = active_game_with_multiple_orders
    url = reverse(viewname, args=[game.id, game.current_phase.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Only one nation's orders
    assert response.data[0]["nation"] == game.members.first().nation
    assert len(response.data[0]["orders"]) == 2

    # Assert resolution is null for active phase orders
    for order in response.data[0]["orders"]:
        assert order["resolution"] is None

@pytest.mark.django_db
def test_list_orders_completed_phase_with_resolutions(authenticated_client, active_game_with_completed_phase_and_resolutions):
    """
    Test listing orders in a completed phase with resolutions.
    """
    game = active_game_with_completed_phase_and_resolutions
    url = reverse(viewname, args=[game.id, game.current_phase.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Only one nation's orders
    
    # Check orders and their resolutions
    nation_data = response.data[0]
    assert len(nation_data["orders"]) == 2
    
    move_order = next(o for o in nation_data["orders"] if o["order_type"] == "Move")
    support_order = next(o for o in nation_data["orders"] if o["order_type"] == "Support")
    
    assert move_order["resolution"]["status"] == "Succeeded"
    assert move_order["resolution"]["by"] is None
    
    assert support_order["resolution"]["status"] == "Invalid support order"
    assert support_order["resolution"]["by"] is None

@pytest.mark.django_db
def test_list_orders_completed_phase_without_resolutions(authenticated_client, active_game_with_multiple_orders):
    """
    Test listing orders in a completed phase without resolutions.
    """
    game = active_game_with_multiple_orders
    phase = game.current_phase
    phase.status = models.Phase.COMPLETED
    phase.save()
    
    url = reverse(viewname, args=[game.id, phase.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1  # Only one nation's orders
    
    # Check that all orders have null resolutions
    for order in response.data[0]["orders"]:
        assert order["resolution"] is None

@pytest.mark.django_db
def test_list_orders_invalid_phase(authenticated_client, active_game_with_multiple_orders):
    """
    Test listing orders for an invalid phase.
    """
    game = active_game_with_multiple_orders
    url = reverse(viewname, args=[game.id, 999])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_list_orders_unauthorized(unauthenticated_client, active_game_with_multiple_orders):
    """
    Test listing orders when not authenticated.
    """
    game = active_game_with_multiple_orders
    url = reverse(viewname, args=[game.id, game.current_phase.id])
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 