import pytest
from django.conf import settings

pytestmark = pytest.mark.skipif(
    not settings._FIREBASE_PROJECT_ID,
    reason="fcm_django is only installed when FIREBASE_PROJECT_ID is configured",
)


@pytest.fixture
def fcm_device_factory(db):
    from fcm_django.models import FCMDevice

    def _create(user, type, registration_id, active=True):
        return FCMDevice.objects.create(
            user=user, type=type, registration_id=registration_id, active=active
        )

    return _create


class TestNotificationDeviceViewSet:
    @pytest.mark.django_db
    def test_registering_new_token_deactivates_previous_active_token_of_same_type(
        self, authenticated_client, primary_user, fcm_device_factory
    ):
        old_device = fcm_device_factory(primary_user, "android", "old-token")

        response = authenticated_client.post(
            "/devices/",
            {"type": "android", "registrationId": "new-token", "active": True},
            format="json",
        )

        assert response.status_code == 201
        old_device.refresh_from_db()
        assert old_device.active is False

    @pytest.mark.django_db
    def test_registering_new_token_does_not_deactivate_devices_of_a_different_type(
        self, authenticated_client, primary_user, fcm_device_factory
    ):
        ios_device = fcm_device_factory(primary_user, "ios", "ios-token")

        response = authenticated_client.post(
            "/devices/",
            {"type": "android", "registrationId": "android-token", "active": True},
            format="json",
        )

        assert response.status_code == 201
        ios_device.refresh_from_db()
        assert ios_device.active is True

    @pytest.mark.django_db
    def test_registering_new_token_does_not_deactivate_other_users_devices(
        self,
        authenticated_client,
        primary_user,
        secondary_user,
        fcm_device_factory,
    ):
        other_user_device = fcm_device_factory(secondary_user, "android", "their-token")

        response = authenticated_client.post(
            "/devices/",
            {"type": "android", "registrationId": "my-token", "active": True},
            format="json",
        )

        assert response.status_code == 201
        other_user_device.refresh_from_db()
        assert other_user_device.active is True

    @pytest.mark.django_db
    def test_disabling_a_device_does_not_deactivate_other_active_devices(
        self, authenticated_client, primary_user, fcm_device_factory
    ):
        web_device = fcm_device_factory(primary_user, "web", "web-token")
        fcm_device_factory(primary_user, "android", "android-token")

        response = authenticated_client.post(
            "/devices/",
            {"type": "android", "registrationId": "android-token", "active": False},
            format="json",
        )

        assert response.status_code == 200
        web_device.refresh_from_db()
        assert web_device.active is True

    @pytest.mark.django_db
    def test_re_registering_same_token_does_not_deactivate_itself(
        self, authenticated_client, primary_user, fcm_device_factory
    ):
        device = fcm_device_factory(primary_user, "android", "same-token")

        response = authenticated_client.post(
            "/devices/",
            {"type": "android", "registrationId": "same-token", "active": True},
            format="json",
        )

        assert response.status_code == 200
        device.refresh_from_db()
        assert device.active is True


class TestDeactivateStaleDevicesCommand:
    @pytest.mark.django_db
    def test_keeps_only_the_newest_active_device_per_user_and_type(
        self, primary_user, fcm_device_factory
    ):
        from django.core.management import call_command

        oldest = fcm_device_factory(primary_user, "android", "token-1")
        middle = fcm_device_factory(primary_user, "android", "token-2")
        newest = fcm_device_factory(primary_user, "android", "token-3")

        call_command("deactivate_stale_devices")

        oldest.refresh_from_db()
        middle.refresh_from_db()
        newest.refresh_from_db()
        assert oldest.active is False
        assert middle.active is False
        assert newest.active is True

    @pytest.mark.django_db
    def test_leaves_devices_of_different_types_untouched(
        self, primary_user, fcm_device_factory
    ):
        from django.core.management import call_command

        android_device = fcm_device_factory(primary_user, "android", "android-token")
        ios_device = fcm_device_factory(primary_user, "ios", "ios-token")

        call_command("deactivate_stale_devices")

        android_device.refresh_from_db()
        ios_device.refresh_from_db()
        assert android_device.active is True
        assert ios_device.active is True

    @pytest.mark.django_db
    def test_leaves_already_inactive_devices_untouched(self, primary_user, fcm_device_factory):
        from django.core.management import call_command

        active_device = fcm_device_factory(primary_user, "android", "active-token")
        inactive_device = fcm_device_factory(
            primary_user, "android", "inactive-token", active=False
        )

        call_command("deactivate_stale_devices")

        active_device.refresh_from_db()
        inactive_device.refresh_from_db()
        assert active_device.active is True
        assert inactive_device.active is False
