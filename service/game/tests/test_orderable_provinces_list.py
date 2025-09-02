import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "orderable-provinces-list"

@pytest.mark.django_db
def test_list_orderable_provinces_success(authenticated_client, active_game_with_phase_options):
    """
    Test successfully listing orderable provinces.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 3  # Should have bud, tri, and vie provinces
    
    # Check structure of response
    province_data = response.data[0]
    assert "province" in province_data
    assert "order" in province_data
    
    # Check province structure
    province = province_data["province"]
    assert "id" in province
    assert "name" in province
    assert "type" in province
    assert "supplyCenter" in province
    
    # Verify we have the expected provinces
    province_ids = [p["province"]["id"] for p in response.data]
    assert "bud" in province_ids
    assert "vie" in province_ids

@pytest.mark.django_db
def test_list_orderable_provinces_with_existing_orders(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when orders already exist.
    """
    # First create some orders using the correct provinces
    create_url = reverse("order-create", args=[active_game_with_phase_options.id])
    
    # Create a hold order
    order_data = {"source": "bud", "order_type": "Hold"}
    create_response = authenticated_client.post(create_url, order_data, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED
    
    # Create a move order
    order_data = {"source": "vie", "target": "tri", "order_type": "Move"}
    create_response = authenticated_client.post(create_url, order_data, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED
    
    # Now test listing orderable provinces
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Find provinces with existing orders
    provinces_with_orders = [p for p in response.data if p["order"] is not None]
    provinces_without_orders = [p for p in response.data if p["order"] is None]
    
    # Should have some provinces with orders
    assert len(provinces_with_orders) == 2  # bud and vie should have orders
    assert len(provinces_without_orders) == 1  # tri should not have an order
    
    # Check order structure for provinces that have orders
    for province_data in provinces_with_orders:
        order = province_data["order"]
        assert "id" in order
        assert "order_type" in order
        assert "source" in order
        assert "target" in order or order["target"] is None
        assert "aux" in order or order["aux"] is None
        assert "resolution" in order

@pytest.mark.django_db
def test_list_orderable_provinces_no_existing_orders(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when no orders exist yet.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # All provinces should have null orders
    for province_data in response.data:
        assert province_data["order"] is None

@pytest.mark.django_db
def test_list_orderable_provinces_game_not_found(authenticated_client):
    """
    Test listing orderable provinces for a non-existent game.
    """
    url = reverse(viewname, args=[999])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_list_orderable_provinces_user_not_a_member(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when user is not a member of the game.
    """
    # Remove the user as a member
    active_game_with_phase_options.members.first().delete()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_list_orderable_provinces_user_eliminated(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when user is eliminated.
    """
    # Mark the member as eliminated
    member = active_game_with_phase_options.members.first()
    member.eliminated = True
    member.save()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_list_orderable_provinces_user_kicked(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when user is kicked.
    """
    # Mark the member as kicked
    member = active_game_with_phase_options.members.first()
    member.kicked = True
    member.save()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_list_orderable_provinces_phase_state_eliminated(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when user's phase state is eliminated.
    """
    # Mark the phase state as eliminated
    phase_state = active_game_with_phase_options.current_phase.phase_states.first()
    phase_state.eliminated = True
    phase_state.save()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_list_orderable_provinces_no_current_phase(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when game has no current phase.
    """
    # Delete the current phase to simulate no current phase
    active_game_with_phase_options.phases.all().delete()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_list_orderable_provinces_no_phase_state(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when user has no phase state.
    """
    # Delete the phase state
    active_game_with_phase_options.current_phase.phase_states.first().delete()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_list_orderable_provinces_unauthorized(unauthenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces when not authenticated.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_list_orderable_provinces_province_display_names(authenticated_client, active_game_with_phase_options):
    """
    Test that province display names are properly returned.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Check that provinces have proper names (not just IDs)
    for province_data in response.data:
        province = province_data["province"]
        assert province["name"] != province["id"]  # Name should be different from ID
        
        # Verify specific expected names
        if province["id"] == "bud":
            assert province["name"] == "Budapest"
        elif province["id"] == "vie":
            assert province["name"] == "Vienna"

@pytest.mark.django_db
def test_list_orderable_provinces_supply_center_info(authenticated_client, active_game_with_phase_options):
    """
    Test that supply center information is correctly included.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Check that supplyCenter field is present and boolean
    for province_data in response.data:
        province = province_data["province"]
        assert "supplyCenter" in province
        assert isinstance(province["supplyCenter"], bool)

@pytest.mark.django_db
def test_list_orderable_provinces_after_creating_order(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces after creating an order.
    """
    # First create an order
    create_url = reverse("order-create", args=[active_game_with_phase_options.id])
    order_data = {
        "source": "bud",
        "order_type": "Hold",
    }
    create_response = authenticated_client.post(create_url, order_data, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED
    
    # Then list orderable provinces
    list_url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(list_url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Find the province with the order
    bud_province = next(p for p in response.data if p["province"]["id"] == "bud")
    assert bud_province["order"] is not None
    assert bud_province["order"]["order_type"] == "Hold"
    assert bud_province["order"]["source"] == "bud"
    
    # Other provinces should still have no orders
    vie_province = next(p for p in response.data if p["province"]["id"] == "vie")
    assert vie_province["order"] is None

@pytest.mark.django_db
def test_list_orderable_provinces_after_updating_order(authenticated_client, active_game_with_phase_options):
    """
    Test listing orderable provinces after updating an existing order.
    """
    create_url = reverse("order-create", args=[active_game_with_phase_options.id])
    
    # First create a hold order
    order_data = {
        "source": "bud",
        "order_type": "Hold",
    }
    create_response = authenticated_client.post(create_url, order_data, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED
    original_order_id = create_response.data["id"]
    
    # Then update it to a move order
    order_data = {
        "source": "bud",
        "target": "tri",
        "order_type": "Move",
    }
    update_response = authenticated_client.post(create_url, order_data, format="json")
    assert update_response.status_code == status.HTTP_201_CREATED
    
    # List orderable provinces
    list_url = reverse(viewname, args=[active_game_with_phase_options.id])
    response = authenticated_client.get(list_url)
    
    assert response.status_code == status.HTTP_200_OK
    
    # Find the province with the updated order
    bud_province = next(p for p in response.data if p["province"]["id"] == "bud")
    assert bud_province["order"] is not None
    assert bud_province["order"]["id"] == original_order_id  # Same order ID
    assert bud_province["order"]["order_type"] == "Move"  # Updated type
    assert bud_province["order"]["source"] == "bud"
    assert bud_province["order"]["target"]["id"] == "tri"  # Updated target province ID
    assert bud_province["order"]["target"]["name"] == "Trieste"  # Updated target province name