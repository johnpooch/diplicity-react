import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "channel-list"

@pytest.mark.django_db
def test_list_channels_as_member(authenticated_client, active_game_with_channels):
    """
    Test that a member can see private channels they're in and all public channels.
    """
    url = reverse(viewname, args=[active_game_with_channels.id])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # Should see private channels they're member of and all public channels
    assert len(response.data) == 2  # private_member_channel + public_channel

    # Verify channel names
    channel_names = [channel["name"] for channel in response.data]
    assert "Private Member" in channel_names
    assert "Public Channel" in channel_names
    assert "Private Non-Member" not in channel_names

@pytest.mark.django_db
def test_list_channels_as_non_member(authenticated_client_for_tertiary_user, active_game_with_channels):
    """
    Test that a non-member can only see public channels.
    """
    url = reverse(viewname, args=[active_game_with_channels.id])
    response = authenticated_client_for_tertiary_user.get(url)
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data) == 1
    channel = response.data[0]
    assert channel["name"] == "Public Channel"

@pytest.mark.django_db
def test_list_channels_unauthenticated(unauthenticated_client, active_game_with_channels):
    """
    Test that unauthenticated users cannot list channels.
    """
    url = reverse(viewname, args=[active_game_with_channels.id])
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 