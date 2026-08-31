import hashlib
import io
import json
import zipfile

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
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


class TestReleaseBundleCommand:

    @pytest.mark.django_db
    def test_publishes_a_bundle_for_both_platforms_by_default(self, dist_directory, bundle_uploads):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
        )
        assert [upload["key"] for upload in bundle_uploads] == [
            "bundles/ios/1.5.10.zip",
            "bundles/android/1.5.10.zip",
        ]
        assert {upload["bucket"] for upload in bundle_uploads} == {"diplicity-bundles"}

    @pytest.mark.django_db
    def test_published_bundle_is_served_to_a_client_on_a_new_enough_binary(
        self, unauthenticated_client, dist_directory, bundle_uploads
    ):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
        )
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert response.data["version"] == "1.5.10"
        assert response.data["url"] == "https://bundles.example.com/bundles/ios/1.5.10.zip"
        assert response.data["checksum"] == hashlib.sha256(bundle_uploads[0]["content"]).hexdigest()

    @pytest.mark.django_db
    def test_published_bundle_is_withheld_from_a_client_on_an_older_binary(
        self, unauthenticated_client, dist_directory, bundle_uploads
    ):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.6.0",
            "--minimum-native-version",
            "1.6.0",
        )
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(version_build="1.5.9"), format="json")
        assert "url" not in response.data

    @pytest.mark.django_db
    def test_zip_holds_the_dist_files_at_its_root(self, dist_directory, bundle_uploads):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
        )
        archive = zipfile.ZipFile(io.BytesIO(bundle_uploads[0]["content"]))
        assert sorted(archive.namelist()) == ["assets/index-abc123.js", "index.html"]
        assert archive.read("index.html") == b"<!doctype html><title>Diplicity</title>"

    @pytest.mark.django_db
    def test_both_platforms_receive_the_same_archive(self, dist_directory, bundle_uploads):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
        )
        assert bundle_uploads[0]["content"] == bundle_uploads[1]["content"]

    @pytest.mark.django_db
    def test_archive_is_uploaded_as_a_zip(self, dist_directory, bundle_uploads):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
        )
        assert bundle_uploads[0]["extra_args"] == {"ContentType": "application/zip"}

    @pytest.mark.django_db
    def test_publishes_only_the_requested_platform(self, unauthenticated_client, dist_directory, bundle_uploads):
        call_command(
            "release_bundle",
            "--dist",
            str(dist_directory),
            "--bundle-version",
            "1.5.10",
            "--minimum-native-version",
            "1.5.9",
            "--platform",
            BundlePlatform.ANDROID,
        )
        assert [upload["key"] for upload in bundle_uploads] == ["bundles/android/1.5.10.zip"]
        url = reverse("update-check")
        response = unauthenticated_client.post(url, plugin_payload(), format="json")
        assert "url" not in response.data

    @pytest.mark.django_db
    def test_refuses_a_version_already_published(self, dist_directory, bundle_uploads, bundle_factory):
        bundle_factory("1.5.10")
        with pytest.raises(CommandError, match="already published"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1.5.10",
                "--minimum-native-version",
                "1.5.9",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_directory_that_is_not_a_built_bundle(self, tmp_path, bundle_uploads):
        empty = tmp_path / "dist"
        empty.mkdir()
        with pytest.raises(CommandError, match="not a built web bundle"):
            call_command(
                "release_bundle",
                "--dist",
                str(empty),
                "--bundle-version",
                "1.5.10",
                "--minimum-native-version",
                "1.5.9",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_non_numeric_version(self, dist_directory, bundle_uploads):
        with pytest.raises(CommandError, match="bundle version 'v1.5.10' is not a dotted numeric version"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "v1.5.10",
                "--minimum-native-version",
                "1.5.9",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_non_numeric_minimum_native_version(self, dist_directory, bundle_uploads):
        with pytest.raises(CommandError, match="minimum native version 'latest'"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1.5.10",
                "--minimum-native-version",
                "latest",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_minimum_native_version_must_be_stated(self, dist_directory, bundle_uploads):
        with pytest.raises(CommandError, match="--minimum-native-version"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1.5.10",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_to_publish_when_bundle_storage_is_unconfigured(self, dist_directory, bundle_uploads):
        with override_settings(R2_BUCKET_NAME="", R2_PUBLIC_BASE_URL=""):
            with pytest.raises(CommandError, match="R2_BUCKET_NAME, R2_PUBLIC_BASE_URL"):
                call_command(
                    "release_bundle",
                    "--dist",
                    str(dist_directory),
                    "--bundle-version",
                    "1.5.10",
                    "--minimum-native-version",
                    "1.5.9",
                )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_version_that_collapses_onto_a_published_one(
        self, dist_directory, bundle_uploads, bundle_factory
    ):
        bundle_factory("1.6")
        with pytest.raises(CommandError, match="already published"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1.6.0",
                "--minimum-native-version",
                "1.5.9",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_version_longer_than_the_column(self, dist_directory, bundle_uploads):
        with pytest.raises(CommandError, match="is longer than 32 characters"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1." + "0" * 40,
                "--minimum-native-version",
                "1.5.9",
            )
        assert bundle_uploads == []

    @pytest.mark.django_db
    def test_refuses_a_minimum_native_version_longer_than_the_column(self, dist_directory, bundle_uploads):
        with pytest.raises(CommandError, match="is longer than 32 characters"):
            call_command(
                "release_bundle",
                "--dist",
                str(dist_directory),
                "--bundle-version",
                "1.5.10",
                "--minimum-native-version",
                "1." + "0" * 40,
            )
        assert bundle_uploads == []
