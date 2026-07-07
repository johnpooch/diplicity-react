from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.utils import timezone

from common.constants import NotificationDeliveryStatus
from notification.models import Notification
from notification.tasks import _attribute_statuses, deliver, prune_old_notifications


def _response(success, exception=None):
    return SimpleNamespace(success=success, message_id="m" if success else None, exception=exception)


class TestAttributeStatuses:
    def test_single_device_success_is_sent(self):
        statuses = _attribute_statuses([1], {"tok": 1}, ["tok"], [_response(True)])
        assert statuses[1] == (NotificationDeliveryStatus.SENT, None)

    def test_single_device_failure_is_failed(self):
        statuses = _attribute_statuses([1], {"tok": 1}, ["tok"], [_response(False, Exception("boom"))])
        assert statuses[1][0] == NotificationDeliveryStatus.FAILED
        assert "boom" in statuses[1][1]

    def test_user_without_token_is_no_device(self):
        statuses = _attribute_statuses([1, 2], {"tok": 1}, ["tok"], [_response(True)])
        assert statuses[2] == (NotificationDeliveryStatus.NO_DEVICE, None)

    def test_multi_device_one_success_is_sent(self):
        statuses = _attribute_statuses(
            [1], {"a": 1, "b": 1}, ["a", "b"], [_response(False, Exception("x")), _response(True)]
        )
        assert statuses[1] == (NotificationDeliveryStatus.SENT, None)

    def test_multi_device_all_failed_is_failed(self):
        statuses = _attribute_statuses(
            [1], {"a": 1, "b": 1}, ["a", "b"], [_response(False, Exception("x")), _response(False, Exception("y"))]
        )
        assert statuses[1][0] == NotificationDeliveryStatus.FAILED


class TestBroadcast:
    @pytest.mark.django_db
    def test_creates_one_pending_row_per_user(self, primary_user, secondary_user):
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id, secondary_user.id],
            title="Test Game",
            body="Deadline approaching",
            notification_type="deadline_warning",
        )

        assert len(rows) == 2
        records = Notification.objects.of_type("deadline_warning")
        assert {r.user_id for r in records} == {primary_user.id, secondary_user.id}
        assert all(r.delivery_status == NotificationDeliveryStatus.PENDING for r in records)

    @pytest.mark.django_db
    def test_persists_content_and_game_id(self, primary_user):
        Notification.objects.broadcast(
            user_ids=[primary_user.id],
            title="My Game",
            body="Some player did not submit orders",
            notification_type="nmr_extension_applied",
            data={"game_id": "my-game", "link": "https://example.com/game/my-game"},
        )

        record = Notification.objects.of_type("nmr_extension_applied").get()
        assert record.title == "My Game"
        assert record.body == "Some player did not submit orders"
        assert record.game_id == "my-game"
        assert record.data == {"game_id": "my-game", "link": "https://example.com/game/my-game"}

    @pytest.mark.django_db
    def test_dedupes_and_drops_none_user_ids(self, primary_user):
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id, primary_user.id, None],
            title="Test",
            body="Body",
            notification_type="game_start",
        )
        assert len(rows) == 1

    @pytest.mark.django_db
    def test_no_rows_for_empty_user_ids(self):
        rows = Notification.objects.broadcast(
            user_ids=[],
            title="Test",
            body="Body",
            notification_type="empty_broadcast_type",
        )
        assert rows == []
        assert not Notification.objects.of_type("empty_broadcast_type").exists()

    @pytest.mark.django_db
    def test_does_not_mutate_caller_data(self, primary_user):
        data = {"game_id": "my-game"}
        Notification.objects.broadcast(
            user_ids=[primary_user.id],
            title="Test",
            body="Body",
            notification_type="game_start",
            data=data,
        )
        assert data == {"game_id": "my-game"}


class TestDeliverNotifications:
    @pytest.mark.django_db
    def test_skipped_when_firebase_unconfigured(self, primary_user, settings):
        settings.FIREBASE_APP = None
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id], title="t", body="b", notification_type="game_start"
        )

        deliver([r.id for r in rows])

        assert Notification.objects.get(id=rows[0].id).delivery_status == NotificationDeliveryStatus.SKIPPED

    @pytest.mark.django_db
    def test_marks_per_user_status_from_response(self, primary_user, secondary_user, settings):
        settings.FIREBASE_APP = object()
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id, secondary_user.id],
            title="t",
            body="b",
            notification_type="game_start",
        )
        response = SimpleNamespace(
            registration_ids_sent=["tok-a"],
            response=SimpleNamespace(responses=[_response(True)]),
        )
        with patch(
            "notification.tasks._fcm_send",
            return_value=(response, {"tok-a": primary_user.id}),
        ):
            deliver([r.id for r in rows])

        by_user = {
            r.user_id: r.delivery_status
            for r in Notification.objects.filter(id__in=[row.id for row in rows])
        }
        assert by_user[primary_user.id] == NotificationDeliveryStatus.SENT
        assert by_user[secondary_user.id] == NotificationDeliveryStatus.NO_DEVICE

    @pytest.mark.django_db
    def test_no_device_when_send_returns_none(self, primary_user, settings):
        settings.FIREBASE_APP = object()
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id], title="t", body="b", notification_type="game_start"
        )
        with patch("notification.tasks._fcm_send", return_value=None):
            deliver([r.id for r in rows])

        assert Notification.objects.get(id=rows[0].id).delivery_status == NotificationDeliveryStatus.NO_DEVICE

    @pytest.mark.django_db
    def test_failed_and_does_not_raise_when_send_errors(self, primary_user, settings):
        settings.FIREBASE_APP = object()
        rows = Notification.objects.broadcast(
            user_ids=[primary_user.id], title="t", body="b", notification_type="game_start"
        )
        with patch("notification.tasks._fcm_send", side_effect=Exception("fcm down")):
            deliver([r.id for r in rows])

        record = Notification.objects.get(id=rows[0].id)
        assert record.delivery_status == NotificationDeliveryStatus.FAILED
        assert "fcm down" in record.error


class TestPruneOldNotifications:
    @pytest.mark.django_db
    def test_prunes_records_older_than_retention_window(self, primary_user, settings):
        settings.NOTIFICATION_RETENTION_DAYS = 30

        old = Notification.objects.create(
            user=primary_user, notification_type="game_start", title="t", body="b"
        )
        recent = Notification.objects.create(
            user=primary_user, notification_type="game_start", title="t", body="b"
        )
        Notification.objects.filter(id=old.id).update(created_at=timezone.now() - timedelta(days=31))

        prune_old_notifications(timestamp=0)

        assert not Notification.objects.filter(id=old.id).exists()
        assert Notification.objects.filter(id=recent.id).exists()
