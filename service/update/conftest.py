import pytest
from django.test import override_settings

from common.constants import BundlePlatform
from update.models import Bundle


@pytest.fixture(autouse=True)
def bundle_base_url():
    with override_settings(R2_PUBLIC_BASE_URL="https://bundles.example.com"):
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
