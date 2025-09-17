import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "interactive-order-create"

@pytest.mark.django_db
def test_interactive_order_create_initial_request(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation with empty selected array (initial request).
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": []}
    
    response = authenticated_client.post(url, data, format="json")
    
    # Should fail because we require at least a province to be selected
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_interactive_order_create_province_selected(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation with province selected.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "select-order-type"
    assert response.data["title"] == "Select order type for Budapest"
    assert not response.data["completed"]
    assert response.data["selected"] == ["bud"]
    
    # Should have order type options
    option_values = [opt["value"] for opt in response.data["options"]]
    assert "Hold" in option_values
    assert "Move" in option_values

@pytest.mark.django_db
def test_interactive_order_create_hold_completion(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for a Hold order (should complete).
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Hold"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "completed"
    assert response.data["title"] == "Budapest will hold"
    assert response.data["completed"]
    assert response.data["selected"] == ["bud", "Hold"]
    assert len(response.data["options"]) == 0
    
    # Verify order was created
    assert "created_order" in response.data
    assert response.data["created_order"] is not None
    assert response.data["created_order"]["order_type"] == "Hold"
    assert response.data["created_order"]["source"]["id"] == "bud"
    assert response.data["created_order"]["target"] is None
    assert response.data["created_order"]["aux"] is None

@pytest.mark.django_db
def test_interactive_order_create_move_target_selection(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for Move order - should show target selection.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Move"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "select-destination"
    assert response.data["title"] == "Select province to move Budapest to"
    assert not response.data["completed"]
    assert response.data["selected"] == ["bud", "Move"]
    
    # Should have target options
    option_values = [opt["value"] for opt in response.data["options"]]
    assert len(option_values) > 0

@pytest.mark.django_db
def test_interactive_order_create_move_completion(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for Move order completion.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Move", "tri"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "completed"
    assert response.data["title"] == "Budapest will move to Trieste"
    assert response.data["completed"]
    assert response.data["selected"] == ["bud", "Move", "tri"]
    assert len(response.data["options"]) == 0
    
    # Verify order was created
    assert "created_order" in response.data
    assert response.data["created_order"] is not None
    assert response.data["created_order"]["order_type"] == "Move"
    assert response.data["created_order"]["source"]["id"] == "bud"
    assert response.data["created_order"]["target"]["id"] == "tri"
    assert response.data["created_order"]["aux"] is None

@pytest.mark.django_db
def test_interactive_order_create_support_auxiliary_selection(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for Support order - should show auxiliary selection.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Support"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "select-auxiliary"
    assert response.data["title"] == "Select province to support for Budapest"
    assert not response.data["completed"]
    assert response.data["selected"] == ["bud", "Support"]
    
    # Should have auxiliary options
    option_values = [opt["value"] for opt in response.data["options"]]
    assert len(option_values) > 0

@pytest.mark.django_db
def test_interactive_order_create_support_target_selection(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for Support order - should show target selection after aux.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Support", "vie"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "select-target"
    assert response.data["title"] == "Select target for support order"
    assert not response.data["completed"]
    assert response.data["selected"] == ["bud", "Support", "vie"]
    
    # Should have target options
    option_values = [opt["value"] for opt in response.data["options"]]
    assert len(option_values) > 0

@pytest.mark.django_db
def test_interactive_order_create_support_completion(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation for Support order completion.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Support", "vie", "tri"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["step"] == "completed"
    assert response.data["title"] == "Budapest will support Vienna to Trieste"
    assert response.data["completed"]
    assert response.data["selected"] == ["bud", "Support", "vie", "tri"]
    assert len(response.data["options"]) == 0
    
    # Verify order was created
    assert "created_order" in response.data
    assert response.data["created_order"] is not None
    assert response.data["created_order"]["order_type"] == "Support"
    assert response.data["created_order"]["source"]["id"] == "bud"
    assert response.data["created_order"]["target"]["id"] == "tri"
    assert response.data["created_order"]["aux"]["id"] == "vie"

@pytest.mark.django_db
def test_interactive_order_create_invalid_province(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation with invalid province.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["invalid"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_interactive_order_create_invalid_order_type(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation with invalid order type.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "InvalidType"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_interactive_order_create_game_not_found(authenticated_client):
    """
    Test interactive order creation for a non-existent game.
    """
    url = reverse(viewname, args=[999])
    data = {"selected": ["bud"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
def test_interactive_order_create_user_not_member(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation when user is not a member of the game.
    """
    # Remove the user as a member
    active_game_with_phase_options.members.first().delete()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_interactive_order_create_user_eliminated(authenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation when user is eliminated.
    """
    # Mark the member as eliminated
    member = active_game_with_phase_options.members.first()
    member.eliminated = True
    member.save()
    
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_interactive_order_create_unauthorized(unauthenticated_client, active_game_with_phase_options):
    """
    Test interactive order creation when not authenticated.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud"]}
    
    response = unauthenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_interactive_order_create_option_labels(authenticated_client, active_game_with_phase_options):
    """
    Test that option labels are properly formatted.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    data = {"selected": ["bud", "Move"]}
    
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["selected"] == ["bud", "Move"]
    
    # Check that options have both value and label
    for option in response.data["options"]:
        assert "value" in option
        assert "label" in option
        # Label should be a proper capitalized province name
        assert option["label"] != option["value"]  # Should be different from value

@pytest.mark.django_db
def test_interactive_order_create_serializer_validation(authenticated_client, active_game_with_phase_options):
    """
    Test request serializer validation.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Test missing selected field
    response = authenticated_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Test invalid selected field type
    response = authenticated_client.post(url, {"selected": "invalid"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Test valid empty array
    response = authenticated_client.post(url, {"selected": []}, format="json")
    # Should fail because OptionsService requires at least province selection
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_interactive_order_create_order_stored_in_database(authenticated_client, active_game_with_phase_options):
    """
    Test that completed interactive orders are actually stored in the database.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Complete a hold order
    data = {"selected": ["bud", "Hold"]}
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["completed"]
    
    # Verify the order exists in the database
    phase_state = active_game_with_phase_options.current_phase.phase_states.first()
    order = models.Order.objects.filter(phase_state=phase_state, source="bud").first()
    
    assert order is not None
    assert order.order_type == "Hold"
    assert order.source == "bud"
    assert order.target is None
    assert order.aux is None

@pytest.mark.django_db
def test_interactive_order_create_order_updates_existing(authenticated_client, active_game_with_phase_options):
    """
    Test that completed interactive orders update existing orders for the same source.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Create first order (Hold)
    data = {"selected": ["bud", "Hold"]}
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["completed"]
    first_order_id = response.data["created_order"]["id"]
    
    # Create second order (Move) for same source
    data = {"selected": ["bud", "Move", "tri"]}
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.data["completed"]
    second_order_id = response.data["created_order"]["id"]
    
    # Should be the same order (updated)
    assert first_order_id == second_order_id
    assert response.data["created_order"]["order_type"] == "Move"
    assert response.data["created_order"]["target"]["id"] == "tri"

@pytest.mark.django_db
def test_interactive_order_create_incomplete_no_order_created(authenticated_client, active_game_with_phase_options):
    """
    Test that incomplete interactive orders do not create actual orders.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Incomplete order (just province selected)
    data = {"selected": ["bud"]}
    response = authenticated_client.post(url, data, format="json")
    
    assert response.status_code == status.HTTP_200_OK
    assert not response.data["completed"]
    assert "created_order" not in response.data or response.data.get("created_order") is None
    
    # Verify no order was created in database
    phase_state = active_game_with_phase_options.current_phase.phase_states.first()
    order = models.Order.objects.filter(phase_state=phase_state, source="bud").first()
    assert order is None

@pytest.mark.django_db
def test_interactive_order_create_validates_order_data(authenticated_client, active_game_with_phase_options):
    """
    Test that interactive order creation validates order data using same rules as regular order creation.
    """
    url = reverse(viewname, args=[active_game_with_phase_options.id])
    
    # Try to create an order that would be invalid according to game rules
    # This should fail with the same validation as the regular create endpoint
    data = {"selected": ["invalid_province", "Hold"]}
    response = authenticated_client.post(url, data, format="json")
    
    # Should fail due to validation
    assert response.status_code == status.HTTP_400_BAD_REQUEST