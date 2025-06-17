import pytest
from django.urls import reverse
from rest_framework import status
from game import models

viewname = "channel-message-create"

@pytest.mark.django_db
def test_create_message_in_private_channel_success(authenticated_client, active_game_with_private_channel, mock_notify_task):
    """
    Test that a member can successfully create a message in a private channel.
    """
    private_channel = active_game_with_private_channel.channels.get(private=True)
    url = reverse(viewname, args=[active_game_with_private_channel.id, private_channel.id])
    payload = {"body": "Hello, world!"}
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    mock_notify_task.assert_called_once()

@pytest.mark.django_db
def test_create_message_in_public_channel_as_member_success(authenticated_client, active_game_with_public_channel, mock_notify_task):
    """
    Test that a member can successfully create a message in a public channel.
    """
    public_channel = active_game_with_public_channel.channels.get(private=False)
    public_channel.members.add(active_game_with_public_channel.members.first())
    
    url = reverse(viewname, args=[active_game_with_public_channel.id, public_channel.id])
    payload = {"body": "Hello in public channel!"}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    mock_notify_task.assert_called_once()

@pytest.mark.django_db
def test_create_message_in_private_channel_as_non_member_fails(authenticated_client_for_secondary_user, active_game_with_private_channel):
    """
    Test that a non-member cannot create a message in a private channel.
    """
    private_channel = active_game_with_private_channel.channels.get(private=True)
    url = reverse(viewname, args=[active_game_with_private_channel.id, private_channel.id])
    payload = {"body": "This should fail"}
    response = authenticated_client_for_secondary_user.post(url, payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
def test_create_message_empty_body(authenticated_client, active_game_with_private_channel):
    """
    Test that creating a message with an empty body returns 400.
    """
    private_channel = active_game_with_private_channel.channels.get(private=True)
    url = reverse(viewname, args=[active_game_with_private_channel.id, private_channel.id])
    payload = {"body": ""}
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
def test_create_message_unauthenticated(unauthenticated_client, active_game_with_private_channel):
    """
    Test that unauthenticated users cannot create a message.
    """
    private_channel = active_game_with_private_channel.channels.get(private=True)
    url = reverse(viewname, args=[active_game_with_private_channel.id, private_channel.id])
    payload = {"body": "Hello, world!"}
    response = unauthenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 