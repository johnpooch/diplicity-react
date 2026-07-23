from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from adjudication import service as adjudication_service
from channel.models import Channel, ChannelMessage
from channel.serializers import ChannelMessageSerializer
from common.constants import DeadlineMode, GameStatus, PhaseFrequency, PhaseStatus
from draw_proposal.models import DrawProposal
from emit.context import build_context
from game.models import Game
from notification.models import Notification, NotificationDelivery
from notification.registry import REGISTRY as NOTIFICATION_REGISTRY
from notification.registry import ChannelMessageSpec
from notification.tasks import PRUNE_AFTER_DAYS, deliver, prune
from phase.models import Phase
from user_profile.models import UserProfile
from victory.models import Victory

User = get_user_model()

_truncate = ChannelMessageSpec._truncate


def _push(event_type):
    return NotificationDelivery.objects.filter(
        notification__event_type=event_type, channel=NotificationDelivery.Channel.PUSH
    )


def _email(event_type):
    return NotificationDelivery.objects.filter(
        notification__event_type=event_type, channel=NotificationDelivery.Channel.EMAIL
    )


def _deliver_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "notification.deliver"]


def _rendered_push(**overrides):
    content = {
        "channel": NotificationDelivery.Channel.PUSH,
        "heading": "Game",
        "body": "Started",
        "link": None,
        "data": None,
    }
    content.update(overrides)
    return [content]


class _StubSpec:
    def __init__(self, rendered):
        self.channels = [content["channel"] for content in rendered]
        self._rendered = rendered

    def render(self, channel):
        return next(content for content in self._rendered if content["channel"] == channel)


def _send_channel_message(channel, member, body):
    serializer = ChannelMessageSerializer(
        context={"channel": channel, "current_game_member": member}
    )
    return serializer.create({"body": body})


def resolve_recipients(event_type, **kwargs):
    context = build_context(event_type, **kwargs)
    return NOTIFICATION_REGISTRY[event_type](context).get_recipients()


def assert_notification(recipient, event_type, **expected):
    qs = Notification.objects.filter(recipient=recipient, event_type=event_type)
    assert qs.exists(), f"No {event_type} notification found for {recipient}"
    notification = qs.latest("created_at")
    delivery = _push(event_type).filter(notification=notification).first()
    assert delivery is not None, f"No push delivery found for {event_type} notification to {recipient}"
    field_map = {"title": "heading"}
    for field, value in expected.items():
        attr = field_map.get(field, field)
        assert getattr(delivery, attr) == value, f"{field}: {getattr(delivery, attr)!r} != {value!r}"
    return delivery


def _create_victory(state, winners):
    game = state["game"]
    phase = Phase.objects.create(
        game=game,
        variant=game.variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status="Completed",
    )
    victory = Victory.objects.create(game=game, winning_phase=phase)
    victory.members.set(winners)
    return victory


class TestTruncateBody:
    def test_short_single_line_unchanged(self):
        assert _truncate("Hello world") == "Hello world"

    def test_exactly_three_lines_unchanged(self):
        text = "line1\nline2\nline3"
        assert _truncate(text) == "line1\nline2\nline3"

    def test_four_lines_truncated_to_three_with_ellipsis(self):
        text = "line1\nline2\nline3\nline4"
        assert _truncate(text) == "line1\nline2\nline3…"

    def test_many_lines_truncated_to_three_with_ellipsis(self):
        text = "\n".join(f"line{i}" for i in range(10))
        assert _truncate(text) == "line0\nline1\nline2…"

    def test_exceeds_max_chars_truncated_with_ellipsis(self):
        long_line = "x" * 250
        result = _truncate(long_line)
        assert result == "x" * 200 + "…"
        assert len(result) == 201

    def test_exceeds_max_chars_after_joining_lines(self):
        line = "x" * 70
        text = f"{line}\n{line}\n{line}"
        result = _truncate(text)
        assert result.endswith("…")
        assert len(result) <= 202

    def test_trailing_whitespace_stripped_before_ellipsis_on_char_limit(self):
        long_line = "x" * 199 + " " + "y" * 50
        result = _truncate(long_line)
        assert not result[:-1].endswith(" ")
        assert result.endswith("…")

    def test_empty_string_unchanged(self):
        assert _truncate("") == ""

    def test_custom_max_lines(self):
        text = "a\nb\nc\nd"
        assert _truncate(text, max_lines=2) == "a\nb…"

    def test_custom_max_chars(self):
        text = "x" * 50
        result = _truncate(text, max_chars=10)
        assert result == "x" * 10 + "…"

    def test_exactly_max_chars_no_ellipsis(self):
        text = "x" * 200
        assert _truncate(text) == "x" * 200


@pytest.fixture
def emit_game(db, game_factory, member_factory, user_factory, classical_variant):
    def _create(with_game_master=False):
        game_master = user_factory() if with_game_master else None
        game = game_factory(variant=classical_variant, game_master=game_master)
        active_one = member_factory(game=game, user=user_factory())
        active_two = member_factory(game=game, user=user_factory())
        eliminated = member_factory(game=game, user=user_factory(), eliminated=True)
        kicked = member_factory(game=game, user=user_factory(), kicked=True)
        civil = member_factory(game=game, user=user_factory(), civil_disorder=True)
        return {
            "game": game,
            "game_master": game_master,
            "active_one": active_one,
            "active_two": active_two,
            "eliminated": eliminated,
            "kicked": kicked,
            "civil": civil,
        }

    return _create


class TestRegistry:
    def test_all_live_notification_types_are_registered(self):
        expected = {
            "channel_message",
            "draw_proposal",
            "game_start",
            "game_draw",
            "game_solo_win",
            "game_solo_loss",
            "phase_resolved",
            "phase_resolved_early",
            "game_deleted",
            "game_admin_reassigned",
            "game_paused",
            "game_resumed",
            "game_deadline_extended",
            "kicked_from_staging",
            "removed_from_staging",
            "civil_disorder",
            "civil_disorder_recovery",
            "elimination",
            "nmr_extension_used",
            "nmr_extension_applied",
            "deadline_warning",
        }
        assert set(NOTIFICATION_REGISTRY) == expected


class TestActiveResolver:
    def test_civil_disorder_excludes_eliminated_kicked_civil_and_includes_game_master(self, emit_game):
        state = emit_game(with_game_master=True)
        result = resolve_recipients("civil_disorder", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["game_master"].id,
        }

    def test_civil_disorder_without_game_master(self, emit_game):
        state = emit_game(with_game_master=False)
        result = resolve_recipients("civil_disorder", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
        }


class TestAllRecipientsResolver:
    @pytest.mark.parametrize(
        "event_type",
        ["game_start", "game_draw", "phase_resolved", "phase_resolved_early"],
    )
    def test_includes_eliminated_and_kicked_and_game_master(self, emit_game, event_type):
        state = emit_game(with_game_master=True)
        result = resolve_recipients(event_type, game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestAllPlayersExceptActorResolver:
    @pytest.mark.parametrize(
        "event_type",
        ["game_paused", "game_resumed", "game_deadline_extended"],
    )
    def test_excludes_the_actor(self, emit_game, event_type):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = resolve_recipients(event_type, game=state["game"], actor=actor)
        assert actor.id not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }

    def test_game_deleted_uses_explicit_recipients(self, emit_game):
        state = emit_game()
        result = resolve_recipients(
            "game_deleted",
            game=state["game"],
            recipients=[state["active_two"].user_id],
        )
        assert result == {state["active_two"].user_id}


class TestActiveExceptActorResolver:
    def test_civil_disorder_recovery_excludes_eliminated_kicked_civil_disorder_and_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = resolve_recipients("civil_disorder_recovery", game=state["game"], actor=actor)
        assert result == {
            state["active_two"].user_id,
            state["game_master"].id,
        }

    @pytest.mark.django_db
    def test_draw_proposal_excludes_eliminated_kicked_civil_disorder_and_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        phase = Phase.objects.create(
            game=state["game"],
            variant=state["game"].variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status="Active",
        )
        proposal = DrawProposal.objects.create(
            game=state["game"], created_by=state["active_one"], phase=phase
        )
        result = resolve_recipients("draw_proposal", draw_proposal=proposal)
        assert result == {
            state["active_two"].user_id,
            state["game_master"].id,
        }


class TestWinnersResolver:
    @pytest.mark.django_db
    def test_solo_win_targets_only_the_winner(self, emit_game):
        state = emit_game(with_game_master=True)
        winner = state["active_one"]
        _create_victory(state, [winner])
        result = resolve_recipients("game_solo_win", game=state["game"])
        assert result == {winner.user_id}

    @pytest.mark.django_db
    def test_solo_loss_excludes_the_winner(self, emit_game):
        state = emit_game(with_game_master=True)
        winner = state["active_one"]
        _create_victory(state, [winner])
        result = resolve_recipients("game_solo_loss", game=state["game"])
        assert winner.user_id not in result
        assert result == {
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestNmrExtensionAppliedResolver:
    def test_includes_all_players_and_game_master(self, emit_game):
        state = emit_game(with_game_master=True)
        result = resolve_recipients("nmr_extension_applied", game=state["game"])
        assert result == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["eliminated"].user_id,
            state["kicked"].user_id,
            state["civil"].user_id,
            state["game_master"].id,
        }


class TestActorResolver:
    def test_nmr_extension_used_targets_only_the_actor(self, emit_game):
        state = emit_game(with_game_master=True)
        actor = state["active_one"].user
        result = resolve_recipients("nmr_extension_used", game=state["game"], actor=actor)
        assert result == {actor.id}


class TestAdminResolver:
    def test_game_admin_reassigned_targets_only_the_admin(self, emit_game):
        state = emit_game()
        game = state["game"]
        game.admin = state["active_one"].user
        game.save(update_fields=["admin"])
        result = resolve_recipients("game_admin_reassigned", game=game)
        assert result == {state["active_one"].user_id}


class TestExplicitResolvers:
    @pytest.mark.parametrize(
        "event_type",
        [
            "kicked_from_staging",
            "removed_from_staging",
            "elimination",
            "deadline_warning",
        ],
    )
    def test_returns_recipients_from_context(self, emit_game, event_type):
        state = emit_game()
        target = state["active_one"].user_id
        result = resolve_recipients(event_type, game=state["game"], recipients=[target])
        assert result == {target}

    def test_empty_when_no_recipients_provided(self, emit_game):
        state = emit_game()
        result = resolve_recipients("elimination", game=state["game"])
        assert result == set()


class TestChannelMessageResolver:
    def test_public_channel_notifies_all_game_members_except_sender(self, emit_game):
        state = emit_game()
        channel = Channel.objects.create(game=state["game"], name="Global", private=False)
        sender = state["active_one"]
        message = ChannelMessage.objects.create(channel=channel, sender=sender, body="hi")
        result = resolve_recipients("channel_message", message=message)
        assert sender.user_id not in result
        assert state["active_two"].user_id in result
        assert state["eliminated"].user_id in result

    def test_private_channel_notifies_only_channel_members_except_sender(self, emit_game):
        state = emit_game()
        channel = Channel.objects.create(game=state["game"], name="Private", private=True)
        sender = state["active_one"]
        channel.members.set([sender, state["active_two"]])
        message = ChannelMessage.objects.create(channel=channel, sender=sender, body="hi")
        result = resolve_recipients("channel_message", message=message)
        assert result == {state["active_two"].user_id}


@pytest.mark.django_db
def test_channel_message_notification_uses_display_name(active_game, in_memory_procrastinate):
    sender_member = active_game.members.first()
    recipient_member = active_game.members.exclude(id=sender_member.id).first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    _send_channel_message(channel, sender_member, "Hello everyone")

    notification = assert_notification(recipient_member.user, "channel_message")
    expected_prefix = f"{sender_member.name}: "
    assert notification.body.startswith(expected_prefix), (
        f"Expected notification body to start with display name '{expected_prefix}', got: '{notification.body}'"
    )
    assert notification.body.split(": ", 1)[0] != sender_member.user.username, (
        f"Notification body should not use username '{sender_member.user.username}' as the sender prefix"
    )


@pytest.mark.django_db
def test_channel_message_notification_deleted_user(active_game, in_memory_procrastinate):
    sender_member = active_game.members.first()
    recipient_member = active_game.members.exclude(id=sender_member.id).first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    sender_member.user = None
    sender_member.save()

    _send_channel_message(channel, sender_member, "Ghost message")

    assert_notification(recipient_member.user, "channel_message", body="Deleted User: Ghost message")


@pytest.mark.django_db
def test_channel_message_notification_masks_sender_in_anonymous_game(active_game, in_memory_procrastinate):
    active_game.anonymous = True
    active_game.save()
    sender_member = active_game.members.first()
    recipient_member = active_game.members.exclude(id=sender_member.id).first()
    channel = Channel.objects.create(game=active_game, name="Global Press", private=False)

    _send_channel_message(channel, sender_member, "Hello everyone")

    notification = assert_notification(recipient_member.user, "channel_message")
    assert notification.body.startswith("Anonymous: ")
    assert sender_member.name not in notification.body


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

        notification = assert_notification(secondary_user, "draw_proposal", title=game.name)
        assert italy.name in notification.body

    @pytest.mark.django_db
    def test_proposer_masked_in_anonymous_game(
        self,
        draw_notification_game_factory,
        secondary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        game.anonymous = True
        game.save()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        notification = assert_notification(
            secondary_user, "draw_proposal", body="Anonymous has proposed a draw. Respond to it now."
        )
        assert italy.name not in notification.body

    @pytest.mark.django_db
    def test_proposer_excluded_from_notification(
        self,
        draw_notification_game_factory,
        primary_user,
        in_memory_procrastinate,
    ):
        game, italy, germany = draw_notification_game_factory()
        DrawProposal.objects.create_proposal(game=game, created_by=italy)

        assert not Notification.objects.filter(recipient=primary_user, event_type="draw_proposal").exists()

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

        assert not Notification.objects.filter(recipient=tertiary_user, event_type="draw_proposal").exists()

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

        assert not Notification.objects.filter(recipient=tertiary_user, event_type="draw_proposal").exists()

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

        assert not Notification.objects.filter(recipient=tertiary_user, event_type="draw_proposal").exists()


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

        game.emit_game_ended()

        for recipient in (primary_user, secondary_user):
            notification = assert_notification(recipient, "game_draw")
            assert italy.name in notification.body
            assert germany.name in notification.body

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

        game.emit_game_ended()

        notification = assert_notification(primary_user, "game_solo_win")
        assert "Congratulations" in notification.body

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

        game.emit_game_ended()

        notification = assert_notification(secondary_user, "game_solo_loss")
        assert italy.name in notification.body
        assert "Better luck" in notification.body


class TestPhaseResolvedNotification:

    def _make_active_phase(self, variant, scheduled_resolution, member_user):
        game = Game.objects.create(
            variant=variant,
            name="Notify Test",
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_frequency=PhaseFrequency.DAILY,
        )
        game.members.create(user=member_user)
        return Phase.objects.create(
            game=game,
            variant=variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=scheduled_resolution,
        )

    @pytest.mark.django_db
    def test_resolution_before_deadline_sends_phase_resolved_early(
        self,
        classical_variant,
        primary_user,
        in_memory_procrastinate,
    ):
        phase = self._make_active_phase(classical_variant, timezone.now() + timedelta(hours=12), primary_user)

        Phase.objects._emit_phase_resolved(phase)

        assert_notification(
            primary_user,
            "phase_resolved_early",
            body=f"{phase.name} resolved early — all players confirmed their orders.",
        )

    @pytest.mark.django_db
    def test_resolution_at_deadline_sends_phase_resolved(
        self,
        classical_variant,
        primary_user,
        in_memory_procrastinate,
    ):
        phase = self._make_active_phase(classical_variant, timezone.now() - timedelta(minutes=1), primary_user)

        Phase.objects._emit_phase_resolved(phase)

        assert_notification(primary_user, "phase_resolved", body=f"{phase.name} has been resolved")

    @pytest.mark.django_db
    def test_game_ending_phase_without_deadline_sends_phase_resolved(
        self,
        classical_variant,
        primary_user,
        in_memory_procrastinate,
    ):
        phase = self._make_active_phase(classical_variant, None, primary_user)

        Phase.objects._emit_phase_resolved(phase)

        assert_notification(primary_user, "phase_resolved")

    @pytest.mark.django_db
    def test_duration_game_early_resolution_still_sends_phase_resolved(
        self,
        classical_variant,
        primary_user,
        in_memory_procrastinate,
    ):
        game = Game.objects.create(
            variant=classical_variant,
            name="Duration Notify Test",
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.DURATION,
        )
        game.members.create(user=primary_user)
        phase = Phase.objects.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=timezone.now() + timedelta(hours=12),
        )

        Phase.objects._emit_phase_resolved(phase)

        assert_notification(primary_user, "phase_resolved")

    @pytest.mark.django_db
    def test_early_resolution_email_subject_marks_resolved_early(
        self,
        classical_variant,
        primary_user,
        in_memory_procrastinate,
    ):
        primary_user.profile.email_notifications_enabled = True
        primary_user.profile.save()
        phase = self._make_active_phase(classical_variant, timezone.now() + timedelta(hours=12), primary_user)

        Phase.objects._emit_phase_resolved(phase)

        delivery = _email("phase_resolved_early").first()
        assert delivery is not None
        assert "Resolved Early" in delivery.heading


class TestGameStartEmailNotification:

    @pytest.mark.django_db
    def test_game_start_defers_email_notification(
        self, pending_game_with_game_master_factory, adjudication_data_classical, in_memory_procrastinate
    ):
        game = pending_game_with_game_master_factory()
        player_count = game.variant.nations.count()
        for i in range(player_count):
            user = User.objects.create_user(f"start_email_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=user, name=f"Start Email Player {i}", email_notifications_enabled=True)
            game.members.create(user=user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        deliveries = _email("game_start")
        assert deliveries.count() == player_count
        assert "Game Started" in deliveries.first().heading
        assert game.name in delivery.heading
        assert game.name in delivery.body


class TestNotificationDeliveryBroadcast:
    @pytest.mark.django_db
    def test_creates_pending_row_per_recipient(self, user_factory, in_memory_procrastinate):
        one, two = user_factory(), user_factory()
        notifications = Notification.objects.bulk_create(
            [Notification(recipient_id=u.id, event_type="phase_resolved") for u in (one, two)]
        )

        NotificationDelivery.objects.broadcast(
            notifications,
            _StubSpec(
                _rendered_push(body="Spring 1901 has been resolved", link="https://example.test/game/1")
            ),
        )

        assert _push("phase_resolved").count() == 2
        for user in (one, two):
            delivery = _push("phase_resolved").get(notification__recipient=user)
            assert delivery.status == NotificationDelivery.Status.PENDING
            assert delivery.body == "Spring 1901 has been resolved"
            assert delivery.link == "https://example.test/game/1"

    @pytest.mark.django_db
    def test_defers_single_batched_deliver_job(self, user_factory, in_memory_procrastinate):
        one, two = user_factory(), user_factory()
        notifications = Notification.objects.bulk_create(
            [Notification(recipient_id=u.id, event_type="game_start") for u in (one, two)]
        )

        NotificationDelivery.objects.broadcast(notifications, _StubSpec(_rendered_push()))

        jobs = _deliver_jobs(in_memory_procrastinate)
        assert len(jobs) == 1
        assert set(jobs[0]["args"]["delivery_ids"]) == set(
            NotificationDelivery.objects.values_list("id", flat=True)
        )


class TestCreateFromEvent:
    @pytest.mark.django_db
    def test_empty_recipients_is_noop(self, game_factory, classical_variant, in_memory_procrastinate):
        game = game_factory(variant=classical_variant)

        created = Notification.objects.create_from_event(
            "elimination", build_context("elimination", game=game, recipients=[])
        )

        assert created == []
        assert Notification.objects.count() == 0
        assert _deliver_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_none_recipient_ids_are_filtered(
        self, user_factory, game_factory, classical_variant, in_memory_procrastinate
    ):
        one = user_factory()
        game = game_factory(variant=classical_variant)

        Notification.objects.create_from_event(
            "elimination", build_context("elimination", game=game, recipients=[one.id, None])
        )

        assert Notification.objects.count() == 1


class TestNotificationDeliver:
    @pytest.mark.django_db
    def test_marks_recipients_sent(self, user_factory, mock_send_notification_to_users, in_memory_procrastinate):
        one = user_factory()
        notifications = Notification.objects.bulk_create(
            [Notification(recipient_id=one.id, event_type="game_start")]
        )
        NotificationDelivery.objects.broadcast(notifications, _StubSpec(_rendered_push()))
        deliveries = NotificationDelivery.objects.filter(notification__in=notifications)

        deliver(delivery_ids=[d.id for d in deliveries])

        for delivery in deliveries:
            delivery.refresh_from_db()
            assert delivery.status == NotificationDelivery.Status.SENT

    @pytest.mark.django_db
    def test_sends_one_batched_push_to_all_recipients(
        self, user_factory, mock_send_notification_to_users, in_memory_procrastinate
    ):
        one, two = user_factory(), user_factory()
        notifications = Notification.objects.bulk_create(
            [Notification(recipient_id=u.id, event_type="game_start") for u in (one, two)]
        )
        NotificationDelivery.objects.broadcast(
            notifications, _StubSpec(_rendered_push(data={"game_id": "1"}))
        )
        deliveries = NotificationDelivery.objects.filter(notification__in=notifications)

        deliver(delivery_ids=[d.id for d in deliveries])

        call = mock_send_notification_to_users.call_args
        assert set(call.kwargs["user_ids"]) == {one.id, two.id}
        assert call.kwargs["notification_type"] == "game_start"
        assert call.kwargs["body"] == "Started"

    @pytest.mark.django_db
    def test_missing_ids_is_noop(self, mock_send_notification_to_users, in_memory_procrastinate):
        deliver(delivery_ids=[9999])

        mock_send_notification_to_users.assert_not_called()


class TestNotificationPrune:
    @pytest.mark.django_db
    def test_prunes_rows_older_than_cutoff(self, user_factory, in_memory_procrastinate):
        one = user_factory()
        old = Notification.objects.bulk_create([Notification(recipient_id=one.id, event_type="game_start")])[0]
        Notification.objects.filter(id=old.id).update(
            created_at=timezone.now() - timedelta(days=PRUNE_AFTER_DAYS + 1)
        )
        recent = Notification.objects.bulk_create([Notification(recipient_id=one.id, event_type="game_start")])[0]

        prune(timestamp=0)

        assert not Notification.objects.filter(id=old.id).exists()
        assert Notification.objects.filter(id=recent.id).exists()
