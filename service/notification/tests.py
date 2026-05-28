import pytest
from channel.models import Channel, ChannelMessage
from notification.signals import _truncate_body


class TestTruncateBody:
    def test_short_single_line_unchanged(self):
        assert _truncate_body("Hello world") == "Hello world"

    def test_exactly_three_lines_unchanged(self):
        text = "line1\nline2\nline3"
        assert _truncate_body(text) == "line1\nline2\nline3"

    def test_four_lines_truncated_to_three_with_ellipsis(self):
        text = "line1\nline2\nline3\nline4"
        assert _truncate_body(text) == "line1\nline2\nline3…"

    def test_many_lines_truncated_to_three_with_ellipsis(self):
        text = "\n".join(f"line{i}" for i in range(10))
        assert _truncate_body(text) == "line0\nline1\nline2…"

    def test_exceeds_max_chars_truncated_with_ellipsis(self):
        long_line = "x" * 250
        result = _truncate_body(long_line)
        assert result == "x" * 200 + "…"
        assert len(result) == 201

    def test_exceeds_max_chars_after_joining_lines(self):
        line = "x" * 70
        text = f"{line}\n{line}\n{line}"
        result = _truncate_body(text)
        assert result.endswith("…")
        assert len(result) <= 202

    def test_trailing_whitespace_stripped_before_ellipsis_on_char_limit(self):
        long_line = "x" * 199 + " " + "y" * 50
        result = _truncate_body(long_line)
        assert not result[:-1].endswith(" ")
        assert result.endswith("…")

    def test_empty_string_unchanged(self):
        assert _truncate_body("") == ""

    def test_custom_max_lines(self):
        text = "a\nb\nc\nd"
        assert _truncate_body(text, max_lines=2) == "a\nb…"

    def test_custom_max_chars(self):
        text = "x" * 50
        result = _truncate_body(text, max_chars=10)
        assert result == "x" * 10 + "…"

    def test_exactly_max_chars_no_ellipsis(self):
        text = "x" * 200
        assert _truncate_body(text) == "x" * 200


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
    assert body.split(": ", 1)[0] != sender_member.user.username, (
        f"Notification body should not use username '{sender_member.user.username}' as the sender prefix"
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
