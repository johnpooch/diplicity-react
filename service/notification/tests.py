import pytest
from channel.models import Channel, ChannelMessage


@pytest.mark.django_db
def test_channel_message_notification_uses_display_name(
    active_game,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Hello everyone")

    mock_send_notification_to_users.assert_called_once()
    call_kwargs = mock_send_notification_to_users.call_args.kwargs
    body = call_kwargs["body"]
    expected_prefix = f"{sender_member.name}: "
    assert body.startswith(expected_prefix), (
        f"Expected notification body to start with display name '{expected_prefix}', got: '{body}'"
    )
    assert sender_member.user.username not in body.split(": ")[0], (
        f"Notification body should not contain username '{sender_member.user.username}' as the sender prefix"
    )


@pytest.mark.django_db
def test_channel_message_notification_deleted_user(
    active_game,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    sender_member.user = None
    sender_member.save()

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Ghost message")

    mock_send_notification_to_users.assert_called_once()
    call_kwargs = mock_send_notification_to_users.call_args.kwargs
    assert call_kwargs["body"].startswith("Deleted User: ")
