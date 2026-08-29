import json

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from common.constants import BundlePlatform, UpdateResponseKind


def plugin_payload(**overrides):
    payload = {
        "platform": BundlePlatform.IOS,
        "app_id": "com.diplicity.app",
        "device_id": "8a3f9c1e-0d4b-4f2a-9c77-2b8e5f1d6a34",
        "custom_id": "",
        "plugin_version": "8.51.15",
        "version_name": "builtin",
        "version_build": "1.5.9",
        "version_code": "159",
        "version_os": "18.5",
        "is_emulator": False,
        "is_prod": True,
    }
    payload.update(overrides)
    return payload


class TestUpdateCheckView:

    @pytest.mark.django_db
    def test_serves_newest_runnable_bundle(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10", checksum="c0ffee")
        bundle_factory("1.5.9")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["version"] == "1.5.10"
        assert response.data["url"] == "https://bundles.example.com/bundles/ios/1.5.10.zip"
        assert response.data["checksum"] == "c0ffee"

    @pytest.mark.django_db
    def test_orders_bundles_numerically_not_lexically(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.9")
        bundle_factory("1.5.10")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.data["version"] == "1.5.10"

    @pytest.mark.django_db
    def test_skips_bundle_the_installed_binary_is_too_old_for(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.6.0", minimum_native_version="1.6.0")
        bundle_factory("1.5.10", minimum_native_version="1.5.0")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.5.9"), format="json")
        assert response.data["version"] == "1.5.10"

    @pytest.mark.django_db
    def test_serves_bundle_when_binary_exactly_meets_minimum(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.6.0", minimum_native_version="1.6.0")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.6.0"), format="json")
        assert response.data["version"] == "1.6.0"

    @pytest.mark.django_db
    def test_no_bundle_runnable_by_the_installed_binary_returns_no_url(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.6.0", minimum_native_version="1.6.0")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.5.9"), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "url" not in response.data
        assert response.data["kind"] == UpdateResponseKind.UP_TO_DATE

    @pytest.mark.django_db
    def test_ignores_bundles_for_another_platform(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10", platform=BundlePlatform.ANDROID)
        bundle_factory("1.5.9", platform=BundlePlatform.IOS)
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.data["version"] == "1.5.9"

    @pytest.mark.django_db
    def test_ignores_inactive_bundles(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10", active=False)
        bundle_factory("1.5.9")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.data["version"] == "1.5.9"

    @pytest.mark.django_db
    def test_no_bundles_at_all_returns_no_url(self, unauthenticated_client):
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "url" not in response.data
        assert response.data["kind"] == UpdateResponseKind.UP_TO_DATE

    @pytest.mark.django_db
    def test_bundle_already_running_returns_no_url(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_name="1.5.10"), format="json")
        assert "url" not in response.data
        assert response.data["kind"] == UpdateResponseKind.UP_TO_DATE

    @pytest.mark.django_db
    def test_older_bundle_still_offered_to_a_client_ahead_of_it(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.9")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_name="1.5.10"), format="json")
        assert response.data["version"] == "1.5.9"

    @pytest.mark.django_db
    def test_unknown_platform_is_rejected(self, unauthenticated_client):
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(platform="web"), format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_missing_platform_is_rejected(self, unauthenticated_client):
        payload = plugin_payload()
        del payload["platform"]
        url = reverse("update-check")
        response = unauthenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_snake_case_request_and_response_keys_survive_camel_case_wiring(
        self, unauthenticated_client, bundle_factory
    ):
        bundle_factory("1.5.10", checksum="c0ffee")
        url = reverse("update-check")
        response = unauthenticated_client.post(
            url,
            data=json.dumps(plugin_payload()),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert set(json.loads(response.content)) == {"version", "url", "checksum"}

    @pytest.mark.django_db
    def test_up_to_date_response_carries_no_url_over_the_wire(self, unauthenticated_client):
        url = reverse("update-check")
        response = unauthenticated_client.post(
            url,
            data=json.dumps(plugin_payload()),
            content_type="application/json",
        )
        assert set(json.loads(response.content)) == {"kind", "message"}

    @pytest.mark.django_db
    def test_two_component_native_version_meets_a_three_component_minimum(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.6.0", minimum_native_version="1.6.0")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.6"), format="json")
        assert response.data["version"] == "1.6.0"

    @pytest.mark.django_db
    def test_non_decimal_version_component_does_not_error(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10")
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.0.\u00b2"), format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_no_bundle_is_served_when_the_public_base_url_is_unset(self, unauthenticated_client, bundle_factory):
        bundle_factory("1.5.10")
        url = reverse("update-check")
        with override_settings(R2_PUBLIC_BASE_URL=""):
            response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert "url" not in response.data
        assert response.data["kind"] == UpdateResponseKind.UP_TO_DATE
