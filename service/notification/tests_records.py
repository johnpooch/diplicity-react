from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from common.constants import NotificationDeliveryStatus
from notification.models import Notification
from notification.tasks import prune_old_notifications
from notification.utils import _delivery_status, send_notification_to_users


class TestDeliveryStatus:
    def test_firebase_unconfigured_is_skipped(self):
        assert _delivery_status(False, True, True) == NotificationDeliveryStatus.SKIPPED
        assert _delivery_status(False, False, False) == NotificationDeliveryStatus.SKIPPED

    def test_configured_without_device_is_no_device(self):
        assert _delivery_status(True, False, True) == NotificationDeliveryStatus.NO_DEVICE

    def test_configured_with_device_and_success_is_sent(self):
        assert _delivery_status(True, True, True) == NotificationDeliveryStatus.SENT

    def test_configured_with_device_and_failure_is_failed(self):
        assert _delivery_status(True, True, False) == NotificationDeliveryStatus.FAILED


class TestRecordNotifications:
    @pytest.mark.django_db
    def test_records_one_row_per_user(self, primary_user, secondary_user):
        send_notification_to_users(
            user_ids=[primary_user.id, secondary_user.id],
            title="Test Game",
            body="Deadline approaching",
            notification_type="deadline_warning",
        )

        records = Notification.objects.order_by("user_id")
        assert records.count() == 2
        assert {r.user_id for r in records} == {primary_user.id, secondary_user.id}

    @pytest.mark.django_db
    def test_persists_content_and_game_id(self, primary_user):
        send_notification_to_users(
            user_ids=[primary_user.id],
            title="My Game",
            body="Some player did not submit orders",
            notification_type="nmr_extension_applied",
            data={"game_id": "my-game", "link": "https://example.com/game/my-game"},
        )

        record = Notification.objects.get()
        assert record.title == "My Game"
        assert record.body == "Some player did not submit orders"
        assert record.notification_type == "nmr_extension_applied"
        assert record.game_id == "my-game"
        assert record.data["type"] == "nmr_extension_applied"
        assert record.data["link"] == "https://example.com/game/my-game"

    @pytest.mark.django_db
    def test_status_is_skipped_when_firebase_unconfigured(self, primary_user):
        send_notification_to_users(
            user_ids=[primary_user.id],
            title="Test",
            body="Body",
            notification_type="game_start",
        )

        assert Notification.objects.get().delivery_status == NotificationDeliveryStatus.SKIPPED

    @pytest.mark.django_db
    def test_no_records_for_empty_user_ids(self):
        send_notification_to_users(
            user_ids=[],
            title="Test",
            body="Body",
            notification_type="game_start",
        )

        assert Notification.objects.count() == 0

    @pytest.mark.django_db
    def test_does_not_mutate_caller_data(self, primary_user):
        data = {"game_id": "my-game"}
        send_notification_to_users(
            user_ids=[primary_user.id],
            title="Test",
            body="Body",
            notification_type="game_start",
            data=data,
        )

        assert data == {"game_id": "my-game"}

    @pytest.mark.django_db
    def test_recording_failure_does_not_break_send(self, primary_user):
        with patch(
            "notification.models.Notification.objects.bulk_create",
            side_effect=Exception("db down"),
        ):
            send_notification_to_users(
                user_ids=[primary_user.id],
                title="Test",
                body="Body",
                notification_type="game_start",
            )

        assert Notification.objects.count() == 0


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
        Notification.objects.filter(id=old.id).update(
            created_at=timezone.now() - timedelta(days=31)
        )

        prune_old_notifications(timestamp=0)

        assert not Notification.objects.filter(id=old.id).exists()
        assert Notification.objects.filter(id=recent.id).exists()
