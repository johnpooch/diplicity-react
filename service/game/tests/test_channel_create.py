import pytest
from django.urls import reverse
from rest_framework import status

viewname = "channel-create"

@pytest.mark.django_db
def test_create_channel_success(authenticated_client, active_game_with_phase_state, secondary_user):
    """
    Test that an authenticated user can successfully create a channel.
    """
    other_member = active_game_with_phase_state.members.create(user=secondary_user, nation="France")

    url = reverse(viewname, args=[active_game_with_phase_state.id])
    payload = {"members": [other_member.id]}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.data
    assert response.data["name"] == "England, France"

@pytest.mark.django_db
def test_create_channel_unauthenticated(unauthenticated_client, active_game_with_phase_state):
    """
    Test that unauthenticated users cannot create a channel.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    payload = {"members": []}
    response = unauthenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_channel_invalid_member(authenticated_client, active_game_with_phase_state):
    """
    Test that creating a channel with an invalid member ID returns 400.
    """
    url = reverse(viewname, args=[active_game_with_phase_state.id])
    payload = {"members": [999]}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST 