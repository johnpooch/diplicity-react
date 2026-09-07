import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.constants import BundlePlatform
from update.models import Bundle
from update.storage import upload_bundle
from update.utils import is_numeric_version, parse_version, sha256_checksum, write_bundle_zip

PLATFORMS = [BundlePlatform.IOS, BundlePlatform.ANDROID]

STORAGE_SETTINGS = [
    "R2_ENDPOINT_URL",
    "R2_BUCKET_NAME",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_PUBLIC_BASE_URL",
]


def object_key_for(platform, version):
    return f"bundles/{platform}/{version}.zip"


class Command(BaseCommand):
    help = "Zip a built web bundle, upload it to bundle storage and register it for over-the-air delivery."

    def add_arguments(self, parser):
        parser.add_argument("--dist", required=True, help="path to the built packages/web dist directory")
        parser.add_argument("--bundle-version", required=True, help="version to publish the bundle under")
        parser.add_argument(
            "--minimum-native-version",
            required=True,
            help="oldest native binary version that can run this bundle",
        )
        parser.add_argument(
            "--platform",
            nargs="+",
            choices=PLATFORMS,
            default=PLATFORMS,
            help="platforms to publish the bundle for",
        )

    def handle(self, *args, **options):
        dist = Path(options["dist"])
        version = options["bundle_version"]
        minimum_native_version = options["minimum_native_version"]
        platforms = list(dict.fromkeys(options["platform"]))

        missing = [name for name in STORAGE_SETTINGS if not getattr(settings, name)]
        if missing:
            raise CommandError(f"bundle storage is not configured: {', '.join(missing)}")

        if not (dist / "index.html").is_file():
            raise CommandError(f"'{dist}' is not a built web bundle: no index.html")

        for label, value, field_name in (
            ("bundle version", version, "version"),
            ("minimum native version", minimum_native_version, "minimum_native_version"),
        ):
            if not is_numeric_version(value):
                raise CommandError(f"{label} '{value}' is not a dotted numeric version")
            max_length = Bundle._meta.get_field(field_name).max_length
            if len(value) > max_length:
                raise CommandError(f"{label} '{value}' is longer than {max_length} characters")

        published = Bundle.objects.filter(platform__in=platforms).values_list("platform", "version")
        taken = sorted({platform for platform, other in published if parse_version(other) == parse_version(version)})
        if taken:
            raise CommandError(f"version '{version}' is already published for {', '.join(taken)}")

        with tempfile.TemporaryDirectory() as directory:
            archive = write_bundle_zip(dist, Path(directory) / f"bundle-{version}.zip")
            checksum = sha256_checksum(archive)
            for platform in platforms:
                upload_bundle(archive, object_key_for(platform, version))

        with transaction.atomic():
            bundles = [
                Bundle.objects.create(
                    version=version,
                    platform=platform,
                    checksum=checksum,
                    object_key=object_key_for(platform, version),
                    minimum_native_version=minimum_native_version,
                )
                for platform in platforms
            ]

        for bundle in bundles:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Published {bundle.platform} bundle {bundle.version} "
                    f"(minimum native version {bundle.minimum_native_version}) to {bundle.url}"
                )
            )
        self.stdout.write(self.style.SUCCESS(f"Checksum {checksum}"))
