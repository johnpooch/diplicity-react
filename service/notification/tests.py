import pytest
from channel.models import Channel, ChannelMessage
from common.constants import GameStatus
from draw_proposal.models import DrawProposal
from victory.models import Victory
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


def _notification_jobs(connector, notification_type=None):
    jobs = [j for j in connector.jobs.values() if j["task_name"] == "notification.send_notification"]
    if notification_type is not None:
        jobs = [j for j in jobs if j["args"].get("notification_type") == notification_type]
    return jobs


def _email_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "email_service.send_email_notification"]


@pytest.mark.django_db
def test_channel_message_notification_uses_display_name(active_game, in_memory_procrastinate):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Hello everyone")

    jobs = _notification_jobs(in_memory_procrastinate, "channel_message")
    assert len(jobs) == 1
    body = jobs[0]["args"]["body"]
    expected_prefix = f"{sender_member.name}: "
    assert body.startswith(expected_prefix), (
        f"Expected notification body to start with display name '{expected_prefix}', got: '{body}'"
    )
    assert body.split(": ", 1)[0] != sender_member.user.username, (
        f"Notification body should not use username '{sender_member.user.username}' as the sender prefix"
    )


@pytest.mark.django_db
def test_channel_message_notification_deleted_user(active_game, in_memory_procrastinate):
    sender_member = active_game.members.first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    sender_member.user = None
    sender_member.save()

    ChannelMessage.objects.create(channel=channel, sender=sender_member, body="Ghost message")

    jobs = _notification_jobs(in_memory_procrastinate, "channel_message")
    assert len(jobs) == 1
    assert jobs[0]["args"]["body"].startswith("Deleted User: ")


class TestDrawProposalNotification:

    @pytest.mark.django_db
    def test_active_member_notified_with_correct_content(
        self,
        draw_notification_game_factory,
        secondary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        jobs = _notification_jobs(in_memory_procrastinate, "draw_proposal")
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert set(args["user_ids"]) == {secondary_user.id}
        assert italy.name in args["body"]
        assert args["title"] == game.name

    @pytest.mark.django_db
    def test_proposer_excluded_from_notification(
        self,
        draw_notification_game_factory,
        primary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        jobs = _notification_jobs(in_memory_procrastinate, "draw_proposal")
        assert primary_user.id not in jobs[0]["args"]["user_ids"]

    @pytest.mark.django_db
    def test_eliminated_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, eliminated=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        jobs = _notification_jobs(in_memory_procrastinate, "draw_proposal")
        assert tertiary_user.id not in jobs[0]["args"]["user_ids"]

    @pytest.mark.django_db
    def test_civil_disorder_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, civil_disorder=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        jobs = _notification_jobs(in_memory_procrastinate, "draw_proposal")
        assert tertiary_user.id not in jobs[0]["args"]["user_ids"]

    @pytest.mark.django_db
    def test_kicked_member_not_notified(
        self,
        draw_notification_game_factory,
        tertiary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.members.create(user=tertiary_user, kicked=True)

        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        jobs = _notification_jobs(in_memory_procrastinate, "draw_proposal")
        assert tertiary_user.id not in jobs[0]["args"]["user_ids"]


class TestGameEndNotifications:

    @pytest.mark.django_db
    def test_draw_notifies_all_members_with_draw_body(
        self,
        end_game_notification_game_factory,
        primary_user,
        secondary_user,
        in_memory_procrastinate,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy, germany)

        game.status = GameStatus.COMPLETED
        game.save()

        jobs = _notification_jobs(in_memory_procrastinate, "game_draw")
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert set(args["user_ids"]) == {primary_user.id, secondary_user.id}
        assert italy.name in args["body"]
        assert germany.name in args["body"]

    @pytest.mark.django_db
    def test_solo_win_sends_congratulations_to_winner(
        self,
        end_game_notification_game_factory,
        primary_user,
        in_memory_procrastinate,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy)

        game.status = GameStatus.COMPLETED
        game.save()

        jobs = _notification_jobs(in_memory_procrastinate, "game_solo_win")
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert primary_user.id in args["user_ids"]
        assert "Congratulations" in args["body"]

    @pytest.mark.django_db
    def test_solo_win_sends_loser_message_to_non_winners(
        self,
        end_game_notification_game_factory,
        secondary_user,
        in_memory_procrastinate,
    ):
        game, phase, italy, germany = end_game_notification_game_factory()
        victory = Victory.objects.create(game=game, winning_phase=phase)
        victory.members.add(italy)

        game.status = GameStatus.COMPLETED
        game.save()

        jobs = _notification_jobs(in_memory_procrastinate, "game_solo_loss")
        assert len(jobs) == 1
        args = jobs[0]["args"]
        assert secondary_user.id in args["user_ids"]
        assert italy.name in args["body"]
        assert "Better luck" in args["body"]


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
