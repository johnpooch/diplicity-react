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
def test_create_message_in_public_channel_without_explicit_members(authenticated_client, game_with_two_members, mock_notify_task):
    """
    Test that a message in a public channel notifies all game members even when the channel has no explicit members.
    This tests the new behavior where public channels notify all game members, not just channel members.
    """
    # Create a public channel with no explicit members
    public_channel = game_with_two_members.channels.create(
        name="Public Press",
        private=False
    )
    
    url = reverse(viewname, args=[game_with_two_members.id, public_channel.id])
    payload = {"body": "Hello in public channel!"}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify that notify_task was called with the correct user IDs
    secondary_user_id = game_with_two_members.members.get(nation="France").user.id
    mock_notify_task.assert_called_once_with(
        args=[[secondary_user_id], {
            "title": "New Message",
            "body": f"primaryuser sent a message in Public Press.",
            "type": "channel_message",
            "game_id": str(game_with_two_members.id),
            "channel_id": str(public_channel.id),
        }],
        kwargs={}
    )

@pytest.mark.django_db
def test_create_message_in_private_channel_notifies_only_channel_members(authenticated_client, game_with_two_members, mock_notify_task):
    """
    Test that a message in a private channel only notifies channel members, not all game members.
    """
    # Create a private channel with only the primary user as member
    private_channel = game_with_two_members.channels.create(
        name="Private Channel",
        private=True
    )
    primary_member = game_with_two_members.members.get(nation="England")
    private_channel.members.add(primary_member)
    
    url = reverse(viewname, args=[game_with_two_members.id, private_channel.id])
    payload = {"body": "Hello in private channel!"}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify that notify_task was called with empty user_ids (no other channel members)
    mock_notify_task.assert_called_once_with(
        args=[[], {
            "title": "New Message",
            "body": f"primaryuser sent a message in Private Channel.",
            "type": "channel_message",
            "game_id": str(game_with_two_members.id),
            "channel_id": str(private_channel.id),
        }],
        kwargs={}
    )

@pytest.mark.django_db
def test_create_message_in_private_channel_with_multiple_members(authenticated_client, game_with_two_members, mock_notify_task):
    """
    Test that a message in a private channel with multiple members notifies the correct users.
    """
    # Create a private channel with both members
    private_channel = game_with_two_members.channels.create(
        name="Private Channel",
        private=True
    )
    primary_member = game_with_two_members.members.get(nation="England")
    secondary_member = game_with_two_members.members.get(nation="France")
    private_channel.members.add(primary_member, secondary_member)
    
    url = reverse(viewname, args=[game_with_two_members.id, private_channel.id])
    payload = {"body": "Hello in private channel!"}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify that notify_task was called with the secondary user's ID
    secondary_user_id = secondary_member.user.id
    mock_notify_task.assert_called_once_with(
        args=[[secondary_user_id], {
            "title": "New Message",
            "body": f"primaryuser sent a message in Private Channel.",
            "type": "channel_message",
            "game_id": str(game_with_two_members.id),
            "channel_id": str(private_channel.id),
        }],
        kwargs={}
    )

@pytest.mark.django_db
def test_create_message_in_public_channel_with_explicit_members_still_notifies_all(authenticated_client, game_with_two_members, mock_notify_task):
    """
    Test that even if a public channel has explicit members, it still notifies all game members.
    This ensures the public channel behavior is consistent regardless of explicit membership.
    """
    # Create a public channel and add both members explicitly
    public_channel = game_with_two_members.channels.create(
        name="Public Press",
        private=False
    )
    primary_member = game_with_two_members.members.get(nation="England")
    secondary_member = game_with_two_members.members.get(nation="France")
    public_channel.members.add(primary_member, secondary_member)
    
    url = reverse(viewname, args=[game_with_two_members.id, public_channel.id])
    payload = {"body": "Hello in public channel!"}
    response = authenticated_client.post(url, payload, format="json")
    
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify that notify_task was called with the secondary user's ID (all game members except sender)
    secondary_user_id = secondary_member.user.id
    mock_notify_task.assert_called_once_with(
        args=[[secondary_user_id], {
            "title": "New Message",
            "body": f"primaryuser sent a message in Public Press.",
            "type": "channel_message",
            "game_id": str(game_with_two_members.id),
            "channel_id": str(public_channel.id),
        }],
        kwargs={}
    )

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