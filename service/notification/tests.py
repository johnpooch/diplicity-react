import pytest
from channel.models import Channel, ChannelMessage
from common.constants import GameStatus
from draw_proposal.models import DrawProposal
from victory.models import Victory
from notification.signals import _truncate_body
from notification.testing import get_notifications


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


def _notification_user_ids(notification_type):
    return {row.user_id for row in get_notifications(notification_type)}


def _email_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "email_service.send_email_notification"]


@pytest.mark.django_db
def test_channel_message_notification_uses_display_name(active_game):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Hello everyone")

    rows = get_notifications("channel_message")
    assert rows
    body = rows[0].body
    expected_prefix = f"{sender_member.name}: "
    assert body.startswith(expected_prefix), (
        f"Expected notification body to start with display name '{expected_prefix}', got: '{body}'"
    )
    assert body.split(": ", 1)[0] != sender_member.user.username, (
        f"Notification body should not use username '{sender_member.user.username}' as the sender prefix"
    )


@pytest.mark.django_db
def test_channel_message_notification_deleted_user(active_game):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    sender_member.user = None
    sender_member.save()

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Ghost message")

    rows = get_notifications("channel_message")
    assert rows
    assert rows[0].body.startswith("Deleted User: ")


@pytest.mark.django_db
def test_channel_message_notification_masks_sender_in_anonymous_game(active_game):
    active_game.anonymous = True
    active_game.save()
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Hello everyone")

    rows = get_notifications("channel_message")
    assert rows
    body = rows[0].body
    assert body.startswith("Anonymous: ")
    assert sender_member.name not in body


class TestDrawProposalNotification:

    @pytest.mark.django_db
    def test_active_member_notified_with_correct_content(
        self,
        draw_notification_game_factory,
        secondary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        rows = get_notifications("draw_proposal")
        assert {row.user_id for row in rows} == {secondary_user.id}
        assert italy.name in rows[0].body
        assert rows[0].title == game.name

    @pytest.mark.django_db
    def test_proposer_masked_in_anonymous_game(
        self,
        draw_notification_game_factory,
        secondary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.anonymous = True
        game.save()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        rows = get_notifications("draw_proposal")
        assert rows
        body = rows[0].body
        assert body == "Anonymous has proposed a draw. Respond to it now."
        assert italy.name not in body

    @pytest.mark.django_db
    def test_proposer_excluded_from_notification(
        self,
        draw_notification_game_factory,
        primary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        assert primary_user.id not in {row.user_id for row in get_notifications("draw_proposal")}

    @pytest.mark.django_db
    def test_eliminated_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, eliminated=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        assert tertiary_user.id not in {row.user_id for row in get_notifications("draw_proposal")}

    @pytest.mark.django_db
    def test_civil_disorder_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, civil_disorder=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        assert tertiary_user.id not in {row.user_id for row in get_notifications("draw_proposal")}

    @pytest.mark.django_db
    def test_kicked_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, kicked=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        assert tertiary_user.id not in {row.user_id for row in get_notifications("draw_proposal")}


class TestGameEndNotifications:

    @pytest.mark.django_db
    def test_draw_notifies_all_members_with_draw_body(
        self,
        end_game_notification_game_factory,
        primary_user,
        secondary_user,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy, germany)

        game.status = GameStatus.COMPLETED
        game.save()

        rows = get_notifications("game_draw")
        assert {row.user_id for row in rows} == {primary_user.id, secondary_user.id}
        assert italy.name in rows[0].body
        assert germany.name in rows[0].body

    @pytest.mark.django_db
    def test_solo_win_sends_congratulations_to_winner(
        self,
        end_game_notification_game_factory,
        primary_user,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy)

        game.status = GameStatus.COMPLETED
        game.save()

        rows = get_notifications("game_solo_win")
        assert primary_user.id in {row.user_id for row in rows}
        assert "Congratulations" in rows[0].body

    @pytest.mark.django_db
    def test_solo_win_sends_loser_message_to_non_winners(
        self,
        end_game_notification_game_factory,
        secondary_user,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy)

        game.status = GameStatus.COMPLETED
        game.save()

        rows = get_notifications("game_solo_loss")
        assert secondary_user.id in {row.user_id for row in rows}
        assert italy.name in rows[0].body
        assert "Better luck" in rows[0].body


class TestGameStartEmailNotification:

    @pytest.mark.django_db
    def test_game_start_defers_email_notification(
        self, end_game_notification_game_factory, in_memory_procrastinate
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        game.status = GameStatus.PENDING
        game.save()

        game.status = GameStatus.ACTIVE
        game.save()

        jobs = _email_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert "Game Started" in args["subject"]
        assert game.name in args["subject"]
        assert game.name in args["html"]
