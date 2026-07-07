from notification.models import Notification


def get_notifications(notification_type=None):
    queryset = Notification.objects.all()
    if notification_type is not None:
        queryset = queryset.filter(notification_type=notification_type)
    return list(queryset.order_by("id"))


def assert_notification(
    notification_type,
    user_ids=None,
    count=None,
    title=None,
    body=None,
    body_contains=None,
    data=None,
    status=None,
):
    rows = get_notifications(notification_type)
    if count is not None:
        assert len(rows) == count, f"expected {count} {notification_type} notifications, got {len(rows)}"
    else:
        assert rows, f"expected at least one {notification_type} notification"
    if user_ids is not None:
        assert {row.user_id for row in rows} == set(user_ids)
    row = rows[0]
    if title is not None:
        assert row.title == title
    if body is not None:
        assert row.body == body
    if body_contains is not None:
        assert body_contains in row.body
    if data is not None:
        assert row.data == data
    if status is not None:
        assert all(row.delivery_status == status for row in rows)
    return rows


def assert_no_notification(notification_type):
    assert not Notification.objects.filter(notification_type=notification_type).exists()
