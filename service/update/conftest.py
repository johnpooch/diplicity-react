import pytest
from django.test import override_settings

from common.constants import BundlePlatform
from update.models import Bundle


@pytest.fixture(autouse=True)
def bundle_storage_settings():
    with override_settings(
        R2_ENDPOINT_URL="https://account.r2.cloudflarestorage.com",
        R2_BUCKET_NAME="diplicity-bundles",
        R2_ACCESS_KEY_ID="access-key-id",
        R2_SECRET_ACCESS_KEY="secret-access-key",
        R2_PUBLIC_BASE_URL="https://bundles.example.com",
    ):
        yield


@pytest.fixture
def bundle_factory(db):
    def _create(
        version,
        platform=BundlePlatform.IOS,
        minimum_native_version="1.0.0",
        active=True,
        checksum="",
    ):
        return Bundle.objects.create(
            version=version,
            platform=platform,
            checksum=checksum,
            object_key=f"bundles/{platform}/{version}.zip",
            minimum_native_version=minimum_native_version,
            active=active,
        )

    return _create


@pytest.fixture
def dist_directory(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Diplicity</title>")
    (dist / "assets" / "index-abc123.js").write_text("console.log('diplicity')")
    return dist


@pytest.fixture
def bundle_uploads(monkeypatch):
    uploads = []

    class StubClient:
        def upload_file(self, filename, bucket, key, **kwargs):
            with open(filename, "rb") as handle:
                uploads.append(
                    {
                        "bucket": bucket,
                        "key": key,
                        "content": handle.read(),
                        "extra_args": kwargs.get("ExtraArgs"),
                    }
                )

    monkeypatch.setattr("update.storage.boto3.client", lambda *args, **kwargs: StubClient())
    return uploads
