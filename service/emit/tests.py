import pytest

import emit
from channel.models import Channel, ChannelEvent
from notification.models import Notification, NotificationDelivery


def _deliver_jobs(connector):
    return [j for j in connector.jobs.values() if j["task_name"] == "notification.deliver"]


def _push(event_type):
    return NotificationDelivery.objects.filter(
        notification__event_type=event_type, channel=NotificationDelivery.Channel.PUSH
    )


def _email(event_type):
    return NotificationDelivery.objects.filter(
        notification__event_type=event_type, channel=NotificationDelivery.Channel.EMAIL
    )


def _build_game_state(game_factory, member_factory, user_factory, classical_variant, with_game_master=False):
    game_master = user_factory() if with_game_master else None
    game = game_factory(variant=classical_variant, game_master=game_master)
    active_one = member_factory(game=game, user=user_factory())
    active_two = member_factory(game=game, user=user_factory())
    return {
        "game": game,
        "game_master": game_master,
        "active_one": active_one,
        "active_two": active_two,
    }


class TestEmitDispatch:
    @pytest.mark.django_db
    def test_push_type_creates_notification_rows_for_resolved_recipients_and_defers_delivery(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant, with_game_master=True)
        emit.emit("game_start", game=state["game"])

        member_ids = set(state["game"].member_user_ids(include_gm=True))
        notifications = Notification.objects.filter(event_type="game_start", recipient_id__in=member_ids)
        assert set(notifications.values_list("recipient_id", flat=True)) == {
            state["active_one"].user_id,
            state["active_two"].user_id,
            state["game_master"].id,
        }
        delivery = _push("game_start").filter(notification__recipient_id__in=member_ids).first()
        assert delivery.heading == state["game"].name
        assert "The game has started" in delivery.body
        assert delivery.data["game_id"] == str(state["game"].id)

        assert len(_deliver_jobs(in_memory_procrastinate)) == 1

    @pytest.mark.django_db
    def test_push_only_type_creates_notification_row(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant)
        emit.emit(
            "elimination",
            game=state["game"],
            recipients=[state["active_one"].user_id],
        )

        notifications = Notification.objects.filter(event_type="elimination")
        assert notifications.count() == 1
        assert notifications.first().recipient_id == state["active_one"].user_id
        assert len(_deliver_jobs(in_memory_procrastinate)) == 1

    @pytest.mark.django_db
    def test_no_notification_or_job_created_when_there_are_no_recipients(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant)
        emit.emit("elimination", game=state["game"], recipients=[])

        assert not Notification.objects.filter(event_type="elimination").exists()
        assert _deliver_jobs(in_memory_procrastinate) == []

    @pytest.mark.django_db
    def test_manager_label_and_deadline_are_inferred_into_copy(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant, with_game_master=True)
        actor = state["active_one"].user
        emit.emit("game_resumed", game=state["game"], actor=actor)

        delivery = _push("game_resumed").first()
        assert delivery.body == f"Game resumed by the Game Master ({actor.username}). New deadline: N/A"

    @pytest.mark.django_db
    def test_email_transport_defers_email_notification(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant)
        for member in (state["active_one"], state["active_two"]):
            member.user.profile.email_notifications_enabled = True
            member.user.profile.save()
        emit.emit("game_start", game=state["game"])

        email_deliveries = _email("game_start")
        assert email_deliveries.count() == 2
        assert "Game Started" in email_deliveries.first().heading

    @pytest.mark.django_db
    def test_channel_event_type_creates_channel_event_on_public_channels(
        self, game_factory, member_factory, user_factory, classical_variant, in_memory_procrastinate
    ):
        state = _build_game_state(game_factory, member_factory, user_factory, classical_variant)
        public = Channel.objects.create(game=state["game"], name="Public Press", private=False)
        private = Channel.objects.create(game=state["game"], name="Secret", private=True)

        emit.emit("game_start", game=state["game"])

        events = ChannelEvent.objects.filter(type="game_start")
        assert set(events.values_list("channel_id", flat=True)) == {public.id}
        assert private.id not in events.values_list("channel_id", flat=True)
